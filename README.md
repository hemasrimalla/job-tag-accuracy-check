# Checking the skill tags on 50 job descriptions

## 1. The check (written before labelling)
- **Scope:** all 50 descriptions, 200 model tags. No sampling.
- **What counts as asked:** a skill from the 54-skill list that the description names in its body. Each is marked *required* (default) or *nice-to-have* (sentence says "Bonus if", "Nice to have" or "is a plus, not a must").
- **Right tag:** on the skill list and *required* in the text.
- **Wrong tag**, three kinds: (a) optional skill tagged, (b) on the list but not in the text, (c) not on the skill list (e.g. "Leadership").
- **Missed skill:** a *required* skill the model did not tag.
- **Synonyms:** a tag counts as right if it is a clear variant of the listed skill (alias table in `alias_table.csv`, e.g. Node = Node.js, Excel = Microsoft Excel). Variants are not errors, but I count them because a matcher joining on the exact list name would miss them.
- **Nice-to-have:** the strict check treats a tag as "this skill is needed", so tagging an optional skill is wrong, and not tagging one is not a miss. I also report a lenient version that accepts optional skills.
- **Tie-break:** judge from the literal text, not from what the job "probably" needs. Soft skills like communication are not on the list, so they cannot be right tags.

## 2. Numbers
| | Count |
|---|---|
| Tags given | 200 |
| Right | 152 |
| Wrong: optional skill tagged | 20 |
| Wrong: on list, not in text | 12 |
| Wrong: not on skill list | 16 |
| Required skills in the text | 177 |
| Missed (required, not tagged) | 25 |

- **Tags right (precision): 152/200 = 76.0%** strict; 172/200 = 86.0% if optional skills are accepted.
- **Skills caught (recall): 152/177 = 85.9%**, so 14.1% of required skills are missed.
- **Descriptions with at least one error:** 40/50 strict, 36/50 lenient. Only 10 are fully clean.
- **Non-canonical names:** 18 right tags, in 16 descriptions, are variants (Excel 5, Node 4, Financial Modeling 4, others 5).

## 3. Three ways it fails
1. **Invented tags (28 tags, 25 descriptions).** 12 tags are on-list skills with no support: Kubernetes (JD007, JD012, JD025), SAP (JD004, JD040, JD044, JD047), Blockchain (JD018, JD030, JD035), Machine Learning (JD005, JD041). 16 tags are soft skills not on the list: Leadership (7, e.g. JD003, JD025), Teamwork (JD001), Problem Solving (JD013, JD027). Only "communication" has a source: every ad says "Good communication matters", and the model tagged Communication in JD023 and JD031.
2. **Optional skills tagged, sometimes in place of required ones (20 tags, 20 descriptions).** The model ignores "bonus" and "plus" wording. Zendesk is tagged as a bonus in JD009, JD039, JD049; SEO in JD004, JD034; Social Media Marketing in JD005, JD035. In JD046 it tags Wireframing (nice to have) but drops Design Systems and Figma (required).
3. **Required skills dropped (25 misses, 20 descriptions).** Typically one item in a list of 3 to 5 is skipped, with no pattern by skill: React (JD002), Git (JD003), Written English (JD019). Some tag lists are very short: JD010 has 1 tag for 3 required skills; JD043 and JD049 miss two each. Invented tags do not explain it: misses also occur without them (14 of the 25 are in descriptions with no invented tag).

## 4. First fix
**Constrain the output to the skill list and make the model quote evidence.** Ask for JSON: for each tag, a name copied exactly from the list, a `required`/`optional` flag, and the phrase from the text that supports it. Reject any tag with no matching phrase or not on the list.
- Why first: it removes pattern 1 (28 of the 48 wrong tags) and the non-canonical names, and the flag fixes pattern 2.
- How to check: re-run on the same 50 plus 50 new descriptions, label with the same rules, and compare. Success = invented tags near 0, optional-as-required tags down, and recall not lower than 85.9%. Watch recall: forcing evidence can make the model drop real skills.

## Files and tool disclosure
`labels.csv` (per description: right, wrong, missing), `alias_table.csv`, `label_tags.py`. Claude (an AI assistant) wrote the labelling script and the first draft of this write-up from my rules; I checked the labels and numbers by hand against the descriptions before submitting. [Edit this line to say what you actually changed.]
