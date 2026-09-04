# Sherlock Home Frontend Roadmap

The frontend roadmap is intentionally separate from the backend/application roadmap.

Backend phases continue to live in [`../ROADMAP.md`](../ROADMAP.md).

This roadmap tracks only the household-facing web experience.

---

## Status Legend

- **DONE** — approved or implemented and validated, depending on the phase.
- **NEXT** — next implementation frontier.
- **PLANNED** — agreed direction but not yet implemented.

---

## F0 — Product Direction and Architecture — DONE

Approved product direction:

- [x] separate frontend roadmap from backend roadmap;
- [x] light mode as the default visual direction;
- [x] dark mode as a user preference;
- [x] friendly detective-boy mascot direction;
- [x] non-oppressive household-finance visual language;
- [x] plain-language replacements for OKR/KPI concepts;
- [x] individual financial goals concept;
- [x] shared household goals concept;
- [x] shared-account UI concept;
- [x] local/private runtime indicators;
- [x] chart accessibility requirement;
- [x] red/green-safe palette concept;
- [x] blue/yellow-safe palette concept;
- [x] web navigation flow;
- [x] dashboard flow;
- [x] Sherlock chat flow;
- [x] settings flow;
- [x] frontend/backend responsibility boundary.

F0 means the **concept and architecture direction are approved**. It does not mean the frontend implementation exists.

---

## F1 — Web Shell and Authenticated Navigation — NEXT

Goal: establish the minimum browser application shell on top of the existing authenticated backend.

Planned work:

- [ ] frontend application entry point;
- [ ] authenticated login page;
- [ ] same-origin authenticated request layer;
- [ ] session-aware application shell;
- [ ] CSRF-compatible state-changing requests;
- [ ] left navigation;
- [ ] route handling;
- [ ] logout;
- [ ] session-expired state;
- [ ] loading state;
- [ ] empty state;
- [ ] error state;
- [ ] local/private runtime status indicator;
- [ ] initial light theme;
- [ ] initial dark theme.

Initial routes:

```text
/login
/dashboard
/transactions
/categories
/goals
/household-goals
/recurring
/alerts
/duplicates
/chat
/settings
```

---

## F2 — Dashboard and Core Financial Views — PLANNED

Goal: expose existing deterministic backend financial capabilities through the browser.

Planned views:

- [ ] monthly spending summary;
- [ ] cash-flow summary;
- [ ] spending-by-category chart;
- [ ] spending evolution chart;
- [ ] transaction list;
- [ ] transaction filters;
- [ ] category breakdown;
- [ ] recurring expenses;
- [ ] anomalies;
- [ ] duplicate-charge candidates;
- [ ] household account summary;
- [ ] accessible text equivalents for charts.

Core principle:

```text
backend deterministic result
        ↓
semantic API data
        ↓
frontend view model
        ↓
chart / table / card
```

---

## F3 — Goals and Household Collaboration — PLANNED

Goal: introduce household-oriented financial planning without exposing corporate OKR/KPI terminology.

Planned concepts:

- [ ] Metas Financeiras;
- [ ] Metas Conjuntas;
- [ ] Progresso;
- [ ] Quanto falta;
- [ ] Prazo;
- [ ] Ritmo atual;
- [ ] account association;
- [ ] household member association;
- [ ] shared-account summaries;
- [ ] individual vs household scope indicators;
- [ ] permission-aware presentation.

Examples:

```text
Guardar R$ 500 por mês
Montar reserva de R$ 10.000
Guardar R$ 20.000 para uma viagem
Reduzir despesas da casa em 8%
```

This phase depends on a backend household/account permission model where required.

The frontend must not simulate authorization that the backend does not enforce.

---

## F4 — Sherlock Web Chat — PLANNED

Goal: expose the current local agent through a household-friendly browser conversation.

Planned work:

- [ ] chat input;
- [ ] answer rendering;
- [ ] conversation loading states;
- [ ] controlled failure states;
- [ ] expandable evidence panel;
- [ ] human-readable evidence descriptions;
- [ ] optional technical tool details;
- [ ] local-model status;
- [ ] local/private processing notice;
- [ ] conversation history strategy.

The browser must call only the authenticated Sherlock API.

It must not invoke Ollama or another model endpoint directly.

---

## F5 — Accessibility and Personalization — PLANNED

Goal: make chart interpretation and application navigation usable across theme and color-vision needs.

Planned settings:

- [ ] Light mode;
- [ ] Dark mode;
- [ ] Standard chart palette;
- [ ] Red/green-safe chart palette;
- [ ] Blue/yellow-safe chart palette;
- [ ] non-color chart indicators;
- [ ] visible keyboard focus;
- [ ] keyboard navigation;
- [ ] accessible chart summaries;
- [ ] meaningful labels for icons;
- [ ] contrast validation;
- [ ] locale-aware BRL formatting.

Charts must never communicate critical meaning through color alone.

---

## F6 — Holmes-Hat Minimum Web Experience — RELEASE GATE

Target release:

```text
v1.0.0 — Holmes-Hat
```

Minimum frontend release gate:

- [ ] authenticated login works from the browser;
- [ ] core web shell is usable;
- [ ] dashboard renders real backend data;
- [ ] transactions are visible;
- [ ] categories are visible;
- [ ] recurring expenses are visible;
- [ ] anomalies are visible;
- [ ] duplicate-charge candidates are visible;
- [ ] Sherlock chat is usable through the browser;
- [ ] local/private runtime status is visible;
- [ ] light/dark preference is available;
- [ ] basic chart accessibility preference is available;
- [ ] browser/API integration is covered by smoke testing;
- [ ] protected financial data is not sent to unapproved external services.

The Holmes-Hat gate does **not** require every richer household-collaboration feature in F3 if that would delay a safe, usable v1.

---

## Deferred Frontend Enhancements

Potential post-Holmes-Hat work:

- richer household member permissions;
- richer account sharing;
- goal notifications;
- household timeline/activity;
- additional accessibility profiles;
- mobile-specific layout;
- installable/PWA behavior;
- printable household summaries;
- richer chart interactions;
- chart export;
- saved dashboard filters;
- household-specific conversational context controls.

---

## Roadmap Rule

Frontend roadmap changes should be documented here.

Backend/application roadmap changes should remain in [`../ROADMAP.md`](../ROADMAP.md).

Cross-cutting release requirements may reference both roadmaps, but the phase histories should not be merged.
