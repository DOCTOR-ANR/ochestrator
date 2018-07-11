//
// Created by Daishi KONDO on 2017/08/07.
//

#include <ndn-cxx/interest.hpp>
#include <ndn-cxx/data.hpp>

#include <boost/bind.hpp>

#include "ndn-firewall.h"

#define TOTAL_ITEMS_IN_WHITELIST 100000
#define TOTAL_ITEMS_IN_BLACKLIST 100000

NdnFirewall::TcpSession::TcpSession(NdnFirewall &ndnFirewall, const std::shared_ptr<Face> &face)
        : m_ndnFirewall(ndnFirewall), m_clientFace(face), m_remoteFace(std::make_shared<Face>(ndnFirewall.m_ios)) {

}

void NdnFirewall::TcpSession::start() {
    m_remoteFace->m_socket.async_connect(m_ndnFirewall.m_remoteEndpoint, boost::bind(&TcpSession::startHandler,
                                                                                     shared_from_this(),
                                                                                     boost::asio::placeholders::error));
}

void NdnFirewall::TcpSession::startHandler(const boost::system::error_code &err) {
    if (!err) {
        std::cout << "session start by " << m_remoteFace->m_socket.remote_endpoint() << std::endl;
        clientReceive();
        remoteReceive();
    } else {
        std::cout << "unable to connect consumer to " << m_ndnFirewall.m_remoteEndpoint << std::endl;
    }
}

void NdnFirewall::TcpSession::clientReceive() {
    boost::asio::async_read(m_clientFace->m_socket, boost::asio::buffer(m_clientBuffer, 8800),
                            boost::asio::transfer_at_least(1),
                            boost::bind(&TcpSession::clientReceiveHandler, shared_from_this(),
                                        boost::asio::placeholders::error,
                                        boost::asio::placeholders::bytes_transferred));
}

void NdnFirewall::TcpSession::clientReceiveHandler(const boost::system::error_code &err, size_t bytes_transferred) {
    if (!err) {
        std::vector<ndn::Interest> interests;
        m_interestFlow.append(m_clientBuffer, bytes_transferred);

        // find the interests in the stream
        findPacket<ndn::Interest>(0x05, m_interestFlow, interests);

        // socket can read again without concurrency issue
        clientReceive();

        std::string forwardBuffer;

        for (auto &interest : interests) {
            std::cout << m_clientFace->m_socket.remote_endpoint() << " send Interest with name="
                      << interest.getName().toUri() << std::endl;
            std::string uri = interest.getName().toUri();

            if (interestPacketFilteringBasedOnNamePrefix(uri)) {
                std::cout << " -> forward to next hop" << std::endl;
                forwardBuffer.append(reinterpret_cast<const char *>(interest.wireEncode().wire()),
                                     interest.wireEncode().size());
            } else {
                std::cout << "the Interest was dropped!!!" << std::endl;
            }
        }
        // forward the other interest(s) to the next hop
        remoteSend(forwardBuffer);
    }
}


void NdnFirewall::TcpSession::clientSend(const std::string &buffer) {
    boost::asio::async_write(m_clientFace->m_socket, boost::asio::buffer(buffer),
                             m_clientFace->m_writeStrand.wrap(boost::bind(&TcpSession::clientSendHandler,
                                                                          shared_from_this(),
                                                                          boost::asio::placeholders::error,
                                                                          boost::asio::placeholders::bytes_transferred)));
}

void NdnFirewall::TcpSession::clientSendHandler(const boost::system::error_code &err, size_t bytes_transferred) {
    if (!err) {

    }
}

void NdnFirewall::TcpSession::remoteReceive() {
    boost::asio::async_read(m_remoteFace->m_socket, boost::asio::buffer(m_remoteBuffer, 8800),
                            boost::asio::transfer_at_least(1),
                            boost::bind(&TcpSession::remoteReceiveHandler, shared_from_this(),
                                        boost::asio::placeholders::error,
                                        boost::asio::placeholders::bytes_transferred));
}

void NdnFirewall::TcpSession::remoteReceiveHandler(const boost::system::error_code &err, size_t bytes_transferred) {
    if (!err) {
        std::vector<ndn::Data> datas;
        m_dataFlow.append(m_remoteBuffer, bytes_transferred);

        // find the data in the stream
        findPacket<ndn::Data>(0x06, m_dataFlow, datas);

        // socket can read again without concurrency issue
        remoteReceive();

        // insert all found datas in the cache
        std::string buffer;
        for (auto &data : datas) {
            std::cout << data.getName() << std::endl;
            buffer.append(reinterpret_cast<const char *>(data.wireEncode().wire()), data.wireEncode().size());
        }

        // send all found datas to client
        clientSend(buffer);
    }
}

void NdnFirewall::TcpSession::remoteSend(const std::string &buffer) {
    boost::asio::async_write(m_remoteFace->m_socket, boost::asio::buffer(buffer),
                             m_remoteFace->m_writeStrand.wrap(boost::bind(&TcpSession::remoteSendHandler,
                                                                          shared_from_this(),
                                                                          boost::asio::placeholders::error,
                                                                          boost::asio::placeholders::bytes_transferred)));
}

void NdnFirewall::TcpSession::remoteSendHandler(const boost::system::error_code &err, size_t bytes_transferred) {
    if (!err) {

    }
}

//----------------------------------------------------------------------------------------------------------------------

// configurations about bits for item and the total items depend on firewall design
// see "Cuckoo Filter: Practically Better Than Bloom" in proceedings of ACM CoNEXT 2014 by Bin Fan, Dave Andersen and Michael Kaminsky
cuckooFilterForFirewall NdnFirewall::m_cuckooFilterForWhiteList(TOTAL_ITEMS_IN_WHITELIST);
cuckooFilterForFirewall NdnFirewall::m_cuckooFilterForBlackList(TOTAL_ITEMS_IN_BLACKLIST);

// need to extract name prefixes (initial pair of (number of slashes, counter) is (0, 0))
// m_slashCounter has to be sorted based on the number of slashes before calling interestPacketFilteringBasedOnNamePrefix function
std::vector<std::pair<uint16_t, uint16_t>> NdnFirewall::m_slashCounter(1, std::make_pair(0, 0));
std::string NdnFirewall::m_mode = "accept";

NdnFirewall::NdnFirewall(size_t concurrency, uint16_t localPort, const std::string &remoteAddress, uint16_t remotePort)
        : Module(concurrency), m_commandFace(m_ios, boost::asio::ip::udp::endpoint(boost::asio::ip::udp::v4(), 6362)),
          m_acceptor(m_ios, boost::asio::ip::tcp::endpoint(boost::asio::ip::tcp::v4(), localPort)),
          m_remoteEndpoint(boost::asio::ip::address::from_string(remoteAddress), remotePort) {
}

NdnFirewall::~NdnFirewall() {

}

void NdnFirewall::run() {
    std::cout << "listen on " << m_acceptor.local_endpoint() << " and will redirect Interests to " << m_remoteEndpoint
              << std::endl;
    receiveCommand();
    accept();
}

bool NdnFirewall::interestPacketFilteringBasedOnNamePrefix(std::string uri) {
    if (m_slashCounter.back().first == 0) {// rule does not exist in both lists
        if (m_mode == "accept") {
            return true;
        } else if (m_mode == "drop") {
            return false;
        }
    } else {
        uint16_t slashCounter = 0;
        std::vector<uint16_t> lengthOfEachNamePrefix;
        uint16_t characterCounter = 0;
        bool breakCheck = false;

        // linear search for slashes
        for (const auto &character : uri) {
            if (character == '/') {
                slashCounter++;
                if (slashCounter != 1) {
                    lengthOfEachNamePrefix.push_back(characterCounter);
                    if (slashCounter == m_slashCounter.back().first) {
                        breakCheck = true;
                        break;
                    }
                }
            }
            characterCounter++;
        }
        // full name also can be name prefix depending on m_slashCounter.back().first
        if (!breakCheck) {
            lengthOfEachNamePrefix.push_back(characterCounter);
        }

        bool whiteListCheck = false;
        bool blackListCheck = false;
        // check if name prefixes (e.g., /a, /a/b) are listed in either white or black list
        for (const auto &length : lengthOfEachNamePrefix) {
            std::string namePrefix = uri.substr(0, length);
            size_t hash = std::hash<std::string>()(namePrefix);
            if (!whiteListCheck && m_cuckooFilterForWhiteList.Contain(hash) ==
                                   cuckoofilter::Ok) {  // once name prefix is found in m_cuckooFilterForWhiteList, no need to check later thanks to name prefix aggregation
                whiteListCheck = true;
                if (blackListCheck) {
                    return true;    // e.g., drop /a, but accept /a/b
                }
            } else if (!blackListCheck && m_cuckooFilterForBlackList.Contain(hash) ==
                                          cuckoofilter::Ok) {   // once name prefix is found in m_cuckooFilterForBlackList, no need to check later thanks to name prefix aggregation
                blackListCheck = true;
                if (whiteListCheck) {
                    return false;   // e.g., accept /a, but drop /a/b
                }
            }
        }
        if (whiteListCheck) {
            return true;    // e.g., accept /a
        } else if (blackListCheck) {
            return false;   // e.g., drop /a
        } else {
            if (m_mode == "accept") {   // accept Interest if the Interest is listed in neither white nor black list
                return true;
            } else if (m_mode == "drop") {  // drop Interest if the Interest is listed in neither white nor black list
                return false;
            }
        }
    }
}

void NdnFirewall::interestPacketMonitoringBasedOnNamePrefix(std::string uri) {
// need to implement later
}

void NdnFirewall::receiveCommand() {
    m_commandFace.async_receive_from(boost::asio::buffer(m_commandBuffer, 65536), m_remoteUdpEndpoint,
                                     boost::bind(&NdnFirewall::commandHandler,
                                                 this,
                                                 boost::asio::placeholders::error,
                                                 boost::asio::placeholders::bytes_transferred));
}

void NdnFirewall::commandHandler(const boost::system::error_code &err, size_t bytes_transferred) {
    if (!err) {
        rapidjson::Document document;
        document.Parse(m_commandBuffer, bytes_transferred);
        if (!document.HasParseError()) {
            bool syntaxCheck = true;
            for (const auto &pair : document.GetObject()) {
                std::string memberName = pair.name.GetString();
                if (memberName != "get" && memberName != "post") {
                    std::string response = R"({"status":"syntax error", "reason":"only 'get' and 'post' are supported"})";
                    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                    syntaxCheck = false;
                    break;
                }
            }
            if (syntaxCheck) {
                for (const auto &pair : document.GetObject()) {
                    std::string memberName = pair.name.GetString();
                    if (memberName == "get") {
                        commandGet(document);
                    } else if (memberName == "post") {
                        commandPost(document);
                    }
                }
            }
        } else {
            std::string response = R"({"status":"syntax error", "reason":"error while parsing"})";
            m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
        }
        receiveCommand();
    } else {
        std::cerr << "command socket error!" << std::endl;
    }
}

void NdnFirewall::commandGet(const rapidjson::Document &document) {
    if (document["get"].IsObject()) {
        bool syntaxCheck = true;
        for (const auto &pair : document["get"].GetObject()) {
            std::string memberName = pair.name.GetString();
            if (memberName != "mode" && memberName != "rules" && memberName != "statistics") {
                std::string response = R"({"status":"syntax error", "reason":"only getting 'mode', 'rules', and 'statistics' are supported"})";
                m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                syntaxCheck = false;
                break;
            }
            if (!document["get"][memberName.c_str()].IsArray()) {
                std::string response = R"({"status":"syntax error", "reason":"value has to be array"})";
                m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                syntaxCheck = false;
                break;
            }
            for (const auto &value : document["get"][memberName.c_str()].GetArray()) {
                if (memberName == "mode") {
                    std::string response = R"({"status":"syntax error", "reason":"'mode' array has to be empty"})";
                    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                    syntaxCheck = false;
                    break;
                } else if (memberName == "rules" && (value != "white" && value != "black")) {
                    std::string response = R"({"status":"syntax error", "reason":"value in 'rules' array has to be 'white' or 'black'"})";
                    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                    syntaxCheck = false;
                    break;
                }
                // perhaps need to write something for "statistics"
//                if (!namePrefix.IsString()) {
//                    std::string response = R"({"status":"fail", "reason":"value in array has to be string"})";
//                    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
//                    syntaxCheck = false;
//                    break;
//                }
            }
            if (!syntaxCheck) {
                break;
            }
        }
        if (syntaxCheck) {
            for (const auto &pair : document["get"].GetObject()) {
                std::string memberName = pair.name.GetString();
                if (memberName == "mode") {
                    std::string response = R"({"mode":")" + m_mode + R"("})";
                    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                } else if (memberName == "rules") {
                    for (const auto &value : document["get"]["rules"].GetArray()) {
                        if (value == "white") {
                            getRules(m_whiteList, value.GetString());
                        } else if (value == "black") {
                            getRules(m_blackList, value.GetString());
                        }
                    }
                } else if (memberName == "statistics") {
                    //        Need to write later
//                    std::cout << memberName << std::endl;
                }
            }
        }
    } else {
        std::string response = R"({"status":"syntax error", "reason":"value has to be object"})";
        m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
    }
}

void NdnFirewall::getRules(const std::set<std::string> &list, const std::string &value) {
    std::string response("[");
    for (const auto &namePrefix : list) {
        response = response + "\"" + namePrefix + "\", ";
    }
    if (response != "[") {   // rules do not exist in white or black list
        response.pop_back();    // ' '
        response.pop_back();    // ','
    }
    response.push_back(']');
    if (value == "white") {
        response = R"({"white list":)" + response + R"(})";
    } else if (value == "black") {
        response = R"({"black list":)" + response + R"(})";
    }
    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
}

void NdnFirewall::commandPost(const rapidjson::Document &document) {
    if (document["post"].IsObject()) {
        bool syntaxCheck = true;
        for (const auto &pair : document["post"].GetObject()) {
            std::string memberName = pair.name.GetString();
            if (memberName != "mode" && memberName != "append-accept" && memberName != "append-drop" &&
                memberName != "delete-accept" && memberName != "delete-drop") {
                std::string response = R"({"status":"syntax error", "reason":"only 'mode', 'append-accept', 'append-drop', 'delete-accept', and 'delete-drop' are supported"})";
                m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                syntaxCheck = false;
                break;
            }
            if (!document["post"][memberName.c_str()].IsArray()) {
                std::string response = R"({"status":"syntax error", "reason":"value has to be array"})";
                m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                syntaxCheck = false;
                break;
            }
            for (const auto &value : document["post"][memberName.c_str()].GetArray()) {
                if (memberName == "mode" && (value != "accept" && value != "drop")) {
                    std::string response = R"({"status":"syntax error", "reason":"value in 'mode' array has to be 'accept' or 'drop'"})";
                    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                    syntaxCheck = false;
                    break;
                } else if (!value.IsString()) {
                    std::string response = R"({"status":"syntax error", "reason":"value in array has to be string"})";
                    m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                    syntaxCheck = false;
                    break;
                }
            }
            if (!syntaxCheck) {
                break;
            }
        }
        if (syntaxCheck) {
            for (const auto &pair : document["post"].GetObject()) {
                std::string memberName = pair.name.GetString();
                if (memberName == "mode") {
                    for (const auto &mode : document["post"]["mode"].GetArray()) {
                        m_mode = mode.GetString();
                    }
                } else if (memberName == "append-accept") {
                    for (const auto &namePrefix : document["post"]["append-accept"].GetArray()) {
                        std::string allowedNamePrefix = namePrefix.GetString();
                        if (m_blackList.find(allowedNamePrefix) != m_blackList.end()) {
                            std::string response = allowedNamePrefix;
                            response = R"({"status":"warning", "reason":"')" + response +
                                       R"(' has been already appended in black list, so that it cannot be appended in white list"})";
                            m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                        } else if (m_whiteList.find(allowedNamePrefix) == m_whiteList.end()) {
                            optimizeList("white", m_whiteList, allowedNamePrefix, m_cuckooFilterForWhiteList);
                        } else {
                            std::string response = allowedNamePrefix;
                            response = R"({"status":"warning", "reason":"')" + response +
                                       R"(' has been already appended in white list"})";
                            m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                        }
                    }
                } else if (memberName == "append-drop") {
                    for (const auto &namePrefix : document["post"]["append-drop"].GetArray()) {
                        std::string deniedNamePrefix = namePrefix.GetString();
                        if (m_whiteList.find(deniedNamePrefix) != m_whiteList.end()) {
                            std::string response = deniedNamePrefix;
                            response = R"({"status":"warning", "reason":"')" + response +
                                       R"(' has been already appended in white list, so that it cannot be appended in black list"})";
                            m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                        } else if (m_blackList.find(deniedNamePrefix) == m_blackList.end()) {
                            optimizeList("black", m_blackList, deniedNamePrefix, m_cuckooFilterForBlackList);
                        } else {
                            std::string response = deniedNamePrefix;
                            response = R"({"status":"warning", "reason":"')" + response +
                                       R"(' has been already appended in black list"})";
                            m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                        }
                    }
                } else if (memberName == "delete-accept") {
                    for (const auto &namePrefix : document["post"]["delete-accept"].GetArray()) {
                        std::string allowedNamePrefix = namePrefix.GetString();
                        auto deletionCheck = m_whiteList.erase(allowedNamePrefix);
                        if (deletionCheck == 0) {
                            std::string response = allowedNamePrefix;
                            response = R"({"status":"warning", "reason":"')" + response +
                                       R"(' does not exist in white list"})";
                            m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                        } else {
                            deleteRules(allowedNamePrefix, m_cuckooFilterForWhiteList);
                        }
                    }
                } else if (memberName == "delete-drop") {
                    for (const auto &namePrefix : document["post"]["delete-drop"].GetArray()) {
                        std::string deniedNamePrefix = namePrefix.GetString();
                        auto deletionCheck = m_blackList.erase(deniedNamePrefix);
                        if (deletionCheck == 0) {
                            std::string response = deniedNamePrefix;
                            response = R"({"status":"warning", "reason":"')" + response +
                                       R"(' does not exist in black list"})";
                            m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                        } else {
                            deleteRules(deniedNamePrefix, m_cuckooFilterForBlackList);
                        }
                    }
                }
            }
        }
    } else {
        std::string response = R"({"status":"syntax error", "reason":"value has to be object"})";
        m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
    }
}

void NdnFirewall::optimizeList(std::string listType, std::set<std::string> &list, const std::string &namePrefix,
                               cuckooFilterForFirewall &cuckooFilter) {
    std::vector<std::string> upperNamePrefixes;    // if name prefix is /a/b/c, this vector is like ["/a", "/a/b"]
    uint16_t slashCounter = 0;
    uint16_t characterCounter = 0;

    // linear search for slashes (for upper name prefixes of name prefix which should be checked)
    for (const char &character : namePrefix) {
        if (character == '/') {
            slashCounter++;
            if (slashCounter != 1) {
                upperNamePrefixes.push_back(namePrefix.substr(0, characterCounter));
            }
        }
        characterCounter++;
    }

    std::string firstNameComponent;

    if (slashCounter == 1) {
        firstNameComponent = namePrefix;
    } else {
        firstNameComponent = upperNamePrefixes[0];
    }

    std::vector<std::string> targetedNamePrefixes;

    // extract from list targeted name prefixes including first name component of name prefix which should be checked
    for (const auto &targetedNamePrefix : list) {
        if (targetedNamePrefix.size() >= firstNameComponent.size() &&
            targetedNamePrefix.compare(0, firstNameComponent.size(), firstNameComponent) == 0) {
            targetedNamePrefixes.push_back(targetedNamePrefix);
        }
    }

    if (targetedNamePrefixes.empty()) {
        appendRules(list, namePrefix, cuckooFilter);
    } else {
        bool skipCheck = false;
        bool cannotAddCheck = false;
        bool insertCheck = false;
        for (const auto &targetedNamePrefix : targetedNamePrefixes) {
            if (!skipCheck) {   // when skipCheck is true, for loop can be skipped
                // check the case that for example /a has already existed in list and name prefix which should be checked is /a/b, so that /a/b can be aggregated
                for (const auto &upperNamePrefix : upperNamePrefixes) {
                    if (targetedNamePrefix == upperNamePrefix) {
                        std::string response = namePrefix;
                        response = R"({"status":"name prefix aggregation in )" + listType + R"( list", "reason":"')" +
                                   response + R"(' can be aggregated into ')" + targetedNamePrefix + R"('"})";
                        m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
                        cannotAddCheck = true;
                        break;
                    }
                }
                if (cannotAddCheck) {
                    break;
                }
            }

            // check the case that for example /a/b has already existed in list and name prefix which should be checked is /a , so that /a/b can be aggregated
            if (targetedNamePrefix.size() >= namePrefix.size() &&
                targetedNamePrefix.compare(0, namePrefix.size(), namePrefix) == 0) {
                if (!insertCheck) {
                    appendRules(list, namePrefix, cuckooFilter);
                    insertCheck = true;
                    skipCheck = true;
                }

                // erase name prefix which exists in list since the name prefix can be aggregated
                list.erase(targetedNamePrefix);
                deleteRules(targetedNamePrefix, cuckooFilter);
                std::string response = namePrefix;
                response = R"({"status":"name prefix aggregation in )" + listType + R"( list", "reason":"')" +
                           targetedNamePrefix + R"(' can be aggregated into ')" + response + R"('"})";
                m_commandFace.send_to(boost::asio::buffer(response), m_remoteUdpEndpoint);
            }
        }
        if (!cannotAddCheck && !insertCheck) {
            appendRules(list, namePrefix, cuckooFilter);
        }
    }
}

void NdnFirewall::appendRules(std::set<std::string> &list, const std::string &namePrefix,
                              cuckooFilterForFirewall &cuckooFilter) {
    list.insert(namePrefix);
    if (m_slashCounter.back().first < (std::count(namePrefix.begin(), namePrefix.end(), '/') + 1)) {
        m_slashCounter.emplace_back(
                static_cast<uint16_t>(std::count(namePrefix.begin(), namePrefix.end(), '/') + 1), 1);
    } else {
        bool counterCheck = false;
        for (auto &eachCounter : m_slashCounter) {
            if (eachCounter.first == (std::count(namePrefix.begin(), namePrefix.end(), '/') + 1)) {
                eachCounter.second++;
                counterCheck = true;
                break;
            }
        }
        if (!counterCheck) {
            m_slashCounter.emplace_back(
                    static_cast<uint16_t>(std::count(namePrefix.begin(), namePrefix.end(), '/') + 1), 1);
            sort(m_slashCounter.begin(), m_slashCounter.end());
        }
    }
    size_t hash = std::hash<std::string>()(namePrefix);
    cuckooFilter.Add(hash);
}

// note that deleteRules function does not erase rules from m_whiteList or m_blackList, which means erase functions of them have to be called
void NdnFirewall::deleteRules(const std::string &namePrefix, cuckooFilterForFirewall &cuckooFilter) {
    uint16_t i = 0;
    for (auto &eachCounter : m_slashCounter) {
        if (eachCounter.first == (std::count(namePrefix.begin(), namePrefix.end(), '/') + 1)) {
            eachCounter.second--;
            if (eachCounter.second == 0) {
                m_slashCounter.erase(m_slashCounter.begin() + i);
            }
            break;
        }
        i++;
    }
    size_t hash = std::hash<std::string>()(namePrefix);
    cuckooFilter.Delete(hash);
}

void NdnFirewall::accept() {
    auto face = std::make_shared<Face>(m_ios);
    m_acceptor.async_accept(face->m_socket, [this, face](const boost::system::error_code &err) {
        accept();
        if (!err) {
            std::make_shared<TcpSession>(*this, face)->start();
        }
    });
}

template<class T>
void NdnFirewall::findPacket(uint8_t packetDelimiter, std::string &stream, std::vector<T> &structure) {
    // find as much as possible packets in the stream
    try {
        do {
            // packet start with the delimiter (for ndn 0x05 or 0x06) so we remove any starting bytes that is not one
            // of them
            stream.erase(0, stream.find(packetDelimiter));

            // select the lenght of the size, according to tlv format (1, 2, 4 or 8 bytes to read)
            uint64_t size = 0;
            switch ((uint8_t) stream[1]) {
                default:
                    size += (uint8_t) stream[1];
                    size += 2;
                    break;
                case 0xFD:
                    size += (uint8_t) stream[2];
                    size <<= 8;
                    size += (uint8_t) stream[3];
                    size += 4;
                    break;
                case 0xFE:
                    size += (uint8_t) stream[2];
                    size <<= 8;
                    size += (uint8_t) stream[3];
                    size <<= 8;
                    size += (uint8_t) stream[4];
                    size <<= 8;
                    size += (uint8_t) stream[5];
                    size += 6;
                    break;
                case 0xFF:
                    size += (uint8_t) stream[2];
                    size <<= 8;
                    size += (uint8_t) stream[3];
                    size <<= 8;
                    size += (uint8_t) stream[4];
                    size <<= 8;
                    size += (uint8_t) stream[5];
                    size <<= 8;
                    size += (uint8_t) stream[6];
                    size <<= 8;
                    size += (uint8_t) stream[7];
                    size <<= 8;
                    size += (uint8_t) stream[8];
                    size <<= 8;
                    size += (uint8_t) stream[9];
                    size += 10;
                    break;
            }

            // check if the stream have enough bytes else wait for more data in the stream
            if (size > ndn::MAX_NDN_PACKET_SIZE) {
                stream.erase(0, 1);
            } else if (size <= stream.size()) {
                // try to build the packet object then remove the read bytes from stream if fail remove the first
                // byte in order to find the next delimiter
                try {
                    structure.emplace_back(ndn::Block(stream.c_str(), size));
                    stream.erase(0, size);
                } catch (std::exception &e) {
                    std::cerr << e.what() << std::endl;
                    stream.erase(0, 1);
                }
            } else {
                break;
            }
        } while (!stream.empty());
    } catch (std::exception &e) {
        std::cerr << e.what() << std::endl;
    }
}