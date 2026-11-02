# Provenance and third-party components

This H1 package adapts the fictional CTS-BRK-0117 rev C product definition and engineering methods from the local brake-thermal-workflow source (observed git HEAD c8b5aa67503b262ab51939542ef9fa20579c20de; working-tree content may differ), and the agent-generated, independently verified methodology from Fusion Product Development. Original projects were read, not modified. docs/source retains the original CTS MD/PDF; it is evidence, not an executable run prompt. LICENSE is retained from brake-thermal-workflow (Apache-2.0).

New/modified H1 work: all role briefs, teaching-first skills, consolidated specifications, handoff definitions, launch prompts, generic MCP client and tests. Differences from source are explicit in DECISIONS.md. Historical outputs, product build/tag/mesh/solve scripts and machine credentials are not included.

SolidPilot: https://github.com/eyfel/mcp-server-solidworks, AGPL-3.0 per predecessor notice. Installed externally, not vendored or modified. Observed local HEAD a81d12ba3752d6282c42a4922e87db8dc26b3f69; installation may include local changes. Preserve its own notices and obligations if distributing/modifying it.

Ansys-agent: existing external Python MCP server with detached jobs and generic source execution. Not copied or modified. Runtime directories are overridden outside OneDrive. Its old scripts are not inputs to the new engineering agents.

PyFluent/PyAnsys: https://fluent.docs.pyansys.com/ and https://geometry.docs.pyansys.com/ . Libraries installed externally; their licenses apply. SolidWorks and Ansys application licenses must be supplied by the operator; no binaries are redistributed.

Hermes: https://hermes-agent.nousresearch.com/docs/ . MCP reference and CLI docs were retrieved successfully; installed CLI and native delegation implementation were inspected to verify actual launch/schema behavior. No global settings, skills or credentials were changed for this package.
