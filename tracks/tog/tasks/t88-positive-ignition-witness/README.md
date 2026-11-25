# Can current heat guarantee a positive regional ignition?

Neither positive rule supplied a witness in any of the **10 windows with an actual shell ignition**. Both deferred all 18 decisions to the native solver. The surviving donor prefix contained all 1,400 serviced sources in each of the 12 multi-frame queries. Charging its guaranteed heat still left the regional decisions open. The two rules close this particular shortcut on the registered Firewoods edits. [Protocol frozen before prediction](PROTOCOL.md) · [Events and decisions per window](SCORE.json)

| Rule | Guaranteed positive windows | Missed positive windows | Queries requiring native replay | Median prediction with preparation | Median paired loaded cost relative to native |
| --- | ---: | ---: | ---: | ---: | ---: |
| Residual heat at the next scan | 0 | 10 | 18 | 0.36 ms | 1.018× |
| Residual heat, then guaranteed graph deposits | 0 | 10 | 18 | 1.92 ms | 1.043× |

The query is the same as T87. It asks whether **any** currently cold, fuel-positive material site immediately outside the second stroke's brush ignites within one, four or eight frames. The native replay observed four positive windows on the original take and six on the reversed take. Both edits use the same asset. The T87 outcomes were known when this test was designed.

## What the rules can guarantee

The ordinary predictor applies the native cooling factor to the present heat and performs the same binary32 store as the next scan. Nonnegative gas deposits before that scan can only increase its value. A cold site with positive fuel and a resulting heat at least the native threshold therefore ignites by this first scan.

For longer windows, the second rule also uses the original serviced frontier prefix. New sites append at the end. Removing an earlier donor can move a surviving prefix donor closer to the front. The predictor subtracts native fuel consumption, including its binary32 stores, through the last required donor step. It keeps only donors whose service is guaranteed. At each eligible recipient, it bounds the donor sum from below by increasing distances, decreasing upward bias, and allowing for binary64 summation and sequential binary32 stores. These deposits enter the following scan. The recurrence applies while the site is cold. If the same site ignites at an earlier scan, it already satisfies the promised deadline. This construction uses no lower bound on future gas heating. The absence of a witness leaves the cause of the actual ignitions unresolved. [Predictor](positive.py) · [Causal answers](PREDICTIONS.json.gz)

## Costs and reference checks

Each query ran independently from its decoded cut. The residual test includes region eligibility and current heat extraction. The graph method starts there and pays for donor selection, regional deposits and remaining scans when needed. Shared asset loading, transforms and both regional ID lists cost 11.91 ms. Reading, hashing, decoding and checking a cut cost 19.82–31.22 ms. Compressed evidence writing for the batch cost 2.38 ms. Adding cut access to the paired comparison gives 2.47× for residual heat and 2.52× for the graph method, excluding the one-time geometry work. Timings are single observations combining separately measured Python and browser costs. No T87 negative predictor ran in this comparison. [Cost breakdown](COSTS.json)

The scorer checked shell membership and input identities against T87. It independently read the archived native per-ID events, confirmed all 18 first-event or end-of-window stopping frames and costs, and tested the deadline of every issued witness. Both predictors returned an empty witness set. Native replay remained the only exact answer for all windows. [Scorer](score.py)

## Reproduce

Use the original pinned T42 PLY and six full checkpoint files from T86 to rerun prediction with NumPy. The scorer requires only the committed artifacts and Python's standard library.

~~~sh
python -B tracks/tog/tasks/t88-positive-ignition-witness/positive.py --asset /path/to/foreground.ply
python -B tracks/tog/tasks/t88-positive-ignition-witness/score.py
~~~
