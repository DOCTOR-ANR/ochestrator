#include "rr-strategy.hpp"

namespace nfd {
	namespace fw {
	    RRStrategy::RRStrategy(Forwarder& forwarder, const Name& name) : Strategy(forwarder) {
            ParsedInstanceName parsed = parseInstanceName(name);
            if (!parsed.parameters.empty()) {
                BOOST_THROW_EXCEPTION(std::invalid_argument("RRStrategy does not accept parameters"));
            }
            if (parsed.version && *parsed.version != getStrategyName()[-1].toVersion()) {
                BOOST_THROW_EXCEPTION(std::invalid_argument("RRStrategy does not support version " + std::to_string(*parsed.version)));
            }
            this->setInstanceName(makeInstanceName(name, getStrategyName()));			
            i=0;
		}

		RRStrategy::~RRStrategy() = default;

        NFD_REGISTER_STRATEGY(RRStrategy);    

        const Name& RRStrategy::getStrategyName() {
            static Name strategyName("/localhost/nfd/strategy/round-robin/%FD%01");
            return strategyName;
        }

		void RRStrategy::afterReceiveInterest(const Face& inFace, const Interest& interest,
                                                const shared_ptr<pit::Entry>& pitEntry) {
			const fib::NextHopList& nexthops = this->lookupFib(*pitEntry).getNextHops();			
            size_t size = nexthops.size();
            auto nexthop_it = nexthops.begin();
			if(i >= size) {
                i = 0;
            }
			unsigned int j = 0;
			while(++j <= i) {
                ++nexthop_it;
            }
			++i;
            Face& outFace = nexthop_it->getFace();
            this->sendInterest(pitEntry, outFace, interest);
		}
	} // namespace fw
} // namespace nfd
