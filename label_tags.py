"""Rule-based labelling of model skill tags against job descriptions.
Reads the two uploaded CSVs, applies the written check, writes labels.csv.
Every judgement is rule-driven so it can be re-run and audited."""
import re, pandas as pd, collections

UP = '/mnt/user-data/uploads/'
skills = pd.read_csv(UP + 'skill-list.csv')['skill'].tolist()
jd = pd.read_csv(UP + 'job-descriptions-tagged.csv')

# Alias table: tag text the model wrote -> canonical skill on the list
ALIAS = {'Node': 'Node.js', 'Excel': 'Microsoft Excel', 'JS': 'JavaScript',
         'ML': 'Machine Learning', 'Postgres': 'PostgreSQL', 'API': 'REST APIs',
         'Financial Modeling': 'Financial Modelling',
         'Social Media': 'Social Media Marketing'}
NICE_CUES = ('bonus if', 'nice to have', 'is a plus')

def canon(tag):
    return ALIAS.get(tag, tag)

def asked_skills(text):
    """Return {skill: 'required'|'nice'} found in the body (title/intro excluded)."""
    sents = [s.strip() for s in re.split(r'(?<=\.)\s+', text)]
    body = sents[1:]                       # sentence 0 repeats the job title
    found = {}
    for s in body:
        level = 'nice' if any(c in s.lower() for c in NICE_CUES) else 'required'
        masked = s
        for sk in sorted(skills, key=len, reverse=True):   # longest first: 'User Research' before 'Research'
            pat = r'(?<![\w.])' + re.escape(sk) + r'(?![\w])'
            if re.search(pat, masked):
                found[sk] = level
                masked = re.sub(pat, ' ', masked)
    return found

rows = []
for _, r in jd.iterrows():
    asked = asked_skills(r.description)
    req = {k for k, v in asked.items() if v == 'required'}
    nice = {k for k, v in asked.items() if v == 'nice'}
    raw = [t.strip() for t in r.model_tags.split(';')]
    right, nice_tag, wrong_unsupported, wrong_offlist, alias_used = [], [], [], [], []
    for t in raw:
        c = canon(t)
        if c != t: alias_used.append(f'{t}->{c}')
        if c not in skills:
            wrong_offlist.append(t)            # not on the skill list (soft skills)
        elif c in req:
            right.append(c)
        elif c in nice:
            nice_tag.append(c)                 # in text, but only optional
        else:
            wrong_unsupported.append(c)        # on list, not in text
    tagged = {canon(t) for t in raw}
    missing = sorted(req - tagged)
    rows.append(dict(jd_id=r.jd_id, title=r.title,
        required_in_text='; '.join(sorted(req)), nice_to_have_in_text='; '.join(sorted(nice)),
        model_tags=r.model_tags, tags_right='; '.join(right),
        tags_wrong_optional_skill='; '.join(nice_tag),
        tags_wrong_not_in_text='; '.join(wrong_unsupported),
        tags_wrong_not_on_skill_list='; '.join(wrong_offlist),
        skills_missing='; '.join(missing), aliases_normalised='; '.join(alias_used),
        n_tags=len(raw), n_right=len(right), n_wrong_optional=len(nice_tag),
        n_wrong_unsupported=len(wrong_unsupported), n_wrong_offlist=len(wrong_offlist),
        n_missing=len(missing), n_required=len(req)))
L = pd.DataFrame(rows)
L.to_csv('labels.csv', index=False)

T = L.n_tags.sum(); R = L.n_right.sum(); O = L.n_wrong_optional.sum()
U = L.n_wrong_unsupported.sum(); F = L.n_wrong_offlist.sum(); M = L.n_missing.sum(); Q = L.n_required.sum()
print('JDs', len(L), 'tags', T, 'required skills in text', Q)
print('right', R, 'optional-as-tag', O, 'not-in-text', U, 'off-list', F, 'missing', M)
print('check R+M=Q', R + M, Q, '| T = R+O+U+F', R + O + U + F)
print(f'strict precision {R}/{T} = {R/T:.1%}   recall {R}/{Q} = {R/Q:.1%}')
print(f'lenient precision {(R+O)}/{T} = {(R+O)/T:.1%}')
err = L[(L.n_wrong_optional + L.n_wrong_unsupported + L.n_wrong_offlist + L.n_missing) > 0]
print('JDs with >=1 error strict', len(err), '; with zero errors', len(L) - len(err))
err2 = L[(L.n_wrong_unsupported + L.n_wrong_offlist + L.n_missing) > 0]
print('JDs with >=1 error lenient', len(err2))
print('alias-only tags', L.aliases_normalised.str.count('->').sum() + (L.aliases_normalised != '').sum() - (L.aliases_normalised != '').sum())
print('JDs with wrong-not-on-list', (L.n_wrong_offlist>0).sum(), '; not-in-text', (L.n_wrong_unsupported>0).sum(),
      '; optional', (L.n_wrong_optional>0).sum(), '; missing', (L.n_missing>0).sum())
for col in ['tags_wrong_not_in_text','tags_wrong_not_on_skill_list','tags_wrong_optional_skill','skills_missing']:
    c = collections.Counter(x for v in L[col].dropna() for x in v.split('; ') if x)
    print(col, dict(c))
    for k in c:
        print('   ', k, list(L[L[col].fillna('').str.contains(re.escape(k))].jd_id))
