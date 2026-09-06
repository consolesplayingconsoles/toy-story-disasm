# Toy Story (Mega Drive) — disassembly pass

Static analysis only (per the smd-disassembly skill: mapping, not a patched
ROM). Start with `log/toystory-notes.md` for the narrative, `log/toystory_facts.py`
for the structured per-game facts, `traces/trace_eu_pal.json` for the raw
recursive-descent trace (EU/PAL ROM), and `scripts/` for the tools used to
produce all of it (rebuilt from scratch this session — see the notes file for why).

Rerun the tracer with extra manual seeds as:

    python3 scripts/trace.py "Toy Story (Europe).gen" out.json <hex_addr> [<hex_addr> ...]
