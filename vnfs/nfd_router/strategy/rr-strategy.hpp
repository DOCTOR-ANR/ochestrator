#ifndef NFD_DAEMON_FW_ROUND_ROBIN_STRATEGY_HPP
#define NFD_DAEMON_FW_ROUND_ROBIN_STRATEGY_HPP

#include "strategy.hpp"

namespace nfd {
	namespace fw {
		class RRStrategy : public Strategy {
			public:
  				RRStrategy(Forwarder& forwarder, const Name& name = getStrategyName());

  			    ~RRStrategy();

                static const Name& getStrategyName();

                void afterReceiveInterest(const Face& inFace, const Interest& interest,
                                          const shared_ptr<pit::Entry>& pitEntry) override;

			private:
				unsigned int i;
		};
	} // namespace fw
} // namespace nfd

#endif // NFD_DAEMON_FW_ROUND_ROBIN_STRATEGY_HPP
