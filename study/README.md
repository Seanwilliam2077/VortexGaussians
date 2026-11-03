# Running the study

The instrument is complete; what it needs is participants. No data has been collected yet.

**Design (pre-registered in the paper):** two-alternative forced choice over five ablations, 18 trials
(6 pairs × 3 repeats), sides counterbalanced, order shuffled, 4 s looping clips, about 5 minutes.
Target N ≥ 12.

## Steps

1. Send each participant this link: <https://seanwilliam2077.github.io/VortexGaussians/study/>
2. They finish on a desktop browser, ideally in a dim room. The page downloads `flame2afc_<id>.csv`.
3. They send you that file. Nothing is uploaded and no personal data is collected.
4. Put the files in `study/results/` and run:

   ```bash
   python study/analyze.py "study/results/*.csv"
   ```

## Rules that are fixed

- Stop at N ≥ 12. Do not look at the table and then decide whether to recruit more.
- No outlier rejection and no response-time filtering. Incomplete sessions stay in.
- Report every tag, including any that goes against the method.
- Do not edit `analyze.py` after the first response arrives; the commit that adds it is the registration.

`tag` values are `solver`, `source`, `interz`, `couple` and `bloom`. `choseA = 1` means the paper's method
or the condition switched on.
