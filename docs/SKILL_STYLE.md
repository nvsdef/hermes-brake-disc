# How skills in this package are written

These rules exist because the H1 skills were too short and too compressed, and
Nemotron could not build the assembly from them. Follow these rules when you add or
edit a skill.

## Layout
```
agents/<role>/SOUL.md                     identity, habits, boundaries (Hermes does NOT inject it into children; AGENTS.md tells them to read it)
agents/<role>/skills/<skill>/SKILL.md     the procedure an agent reasons with
agents/<role>/skills/<skill>/references/  long detail, loaded on demand with skill_view(name, path)
agents/_shared/skills/brake-handoff/      the cross-stage contract, loaded by every role
```
Skill names are prefixed by role: `brake-lead-*`/`brake-*` (lead), `sw-*`,
`sc-*`, `fl-*`. This makes ownership obvious in `skills_list()`.

## Frontmatter (Hermes)
```yaml
---
name: sw-rotor-build
description: "Build and gate the 23 rotor bodies in SolidWorks."   # <= 60 characters, quoted
version: 1.0.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, solidworks]
---
```

## Content rules
1. **Guidance, not automation.** Skills teach the method, the traps and the
   checks. They never ship a runnable stage script (no `build.py`, `tag.py`,
   `mesh.py` or `solve.py`). Short API idioms of 1 to 15 lines are encouraged when
   an exact call signature or argument is the thing that goes wrong. Label each one
   "API idiom", not "run this".
2. **Concrete numbers beat adjectives.** Every step ends with an explicit check
   against a PRD section 4 or section 5 number: `expected / measured / tolerance`.
3. **Write out the traps.** Keep every "the tool reports success but did X" finding
   from the predecessor, with its measured evidence. These are the most valuable
   lines in the package.
4. **Readable text.** Put spaces between words and numbers (`within 1 %`, not
   `within1%`). Use ASCII minus signs and the word "to" for ranges
   (`z = -16 to -6`). Write units on every number. Use full sentences with short
   paragraphs, and tables for anything that has columns.
5. **Numbered procedures with completion criteria.** Each step says what "done"
   looks like in measurable terms, and what to do on a miss.
6. **HALT protocol is explicit.** Two repairs, then stop and report both numbers.
7. **Tool names.** Use the bare MCP tool name, for example `create_sketch`. Hermes
   exposes it with a server prefix (`mcp_solidpilot_create_sketch` or
   `mcp__solidpilot__create_sketch`). Tell the agent to match on the suffix.
8. **Geometry authority.** Skills never restate dimensions differently from
   `specs/PRD.md`. Quote the PRD section, or copy the number exactly.
9. **No history as a target.** Predecessor measurements can illustrate a trap. They
   are never acceptance values. The PRD checksums are the acceptance values.
10. Every SKILL.md ends with a `## Verification` section.
