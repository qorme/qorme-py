# Sampling

Sampling is a technique used to reduce the amount of data collected and sent to the server, hence reducing the overhead.

## Sampling methodology

Sampling is implemented by specifying how much contexts a tracking domain should handle per interval (e.g 100 context per minute).

For example, if a tracking domain is set to handle n contexts per interval (e.g 100 context per minute), and the server receives 200 contexts in a minute, the tracking domain will only handle 100 contexts, and the rest will be discarded. Also have a limit for the number of contexts tracked in 24 hours. Individual tracking domains can be time limited, for example no more than half of the interval.

This is done by checking the number of contexts received in the last minute, and if it exceeds the specified limit, the tracking domain will not handle any more contexts for the rest of the minute.

However, we don't want all the tracking domains to be active for say 20s then inactive for the rest of the minute.

Some domains might be active at the start and others at the end of the minute.

If all the domains happen to reach their limit before the minute is over, all tracking is disabled for the rest of the minute.

This mechanism works well with traffic since when there is a lot of traffic we have enough data, if there isn't we have all the data we could have. It's a win-win situation.

Tracking domains can still ignore some contexts while they're enabled. For example it would make more sense for the query plan domain to retrieve the plan for queries with different SQL statements. Otherwise, it would be a waste of resources. Same remark for traceback domain with the difference that traceback domain may need more than just sql to see if it should skip a query

Management command domain tracker can stay a long time without having to handle any context so need to find a mechanism to force disable some domains. Maybe only activate it when running an actual management command.

Have tracking domains add their overhead estimate from low to high and orchestrate accordingly. 2 high shouldn't be active at the same time (e.g traceback and attributes). For example:

- 3: 3 low, 2 low + 1 medium, 2 low + 1 high, 1 low + 1 medium + 1 high
- 2: 2 medium, 2 low, 1 medium + 1 low, 1 high + 1 low, 1 medium + 1 high
- 1: 1 high, 1 low, 1 medium

## To Do

Add a seeting that controls how much context a domain can be active in. For example. 20% means a domain wil be active for 20 contexts and inactive for the other 80.

The final setup may look like:
- Handle at most 1k contexts per hour
- Activate tracking for at most 45 minutes every hour
- For each, enable tracking relative to its ratio
