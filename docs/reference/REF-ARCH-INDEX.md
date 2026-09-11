# Reference Architecture — Multi-Agent URL Index

Every URL appears **exactly once**, under the question that owns it. Other questions
it answers are listed in `Also`. Built from `urls.csv` by `STARTER/build_refarch_index.py`.

| Run | Short | URLs |
|---|---|---:|
| cursor | `cur` | 1230 |
| fable-5-1-claude-code | `fab` | 3028 |
| kimi-k3-cursor | `kim` | 1590 |
| url-index-gpt-5.6-sol-chatgpt-v2.0 | `gpt` | 389 |

**5828 unique URLs** across 2176 domains, 244 questionnaire questions.

## Trust

| Band | Tier | Means |
|---|---|---|
| `core` | T1 | standards body / formal spec |
| `primary` | T2 | primary implementation / official docs |
| `research` | T3 | engineering or security research |
| **`WILD`** | U | **untiered — unknown source. Treat as unsourced.** |

1646 of 5828 rows are WILD (28%).

`†` marks an undated row (4178 of 5828). Undated is **not** the same as untrusted: a living spec page carries no publication date, and 317 of 435 T1 rows are undated. Bucket carries recency for rows that do have a date.

Buckets are relative to the reference date 2026-09-10: **B1** within 3 months · **B2** within 9 months · **B3** older or undated.

Src: `age` engine page-age · `exc` date in excerpt · `url` date in URL · `—` none.

---

## U. Universal questions

### U.1

**Q:** What is the port (interface) the platform depends on? Published standard, de facto standard, or ours?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/buildpack/spec/blob/master/platform.md |
| primary | B3 | T2 | — † | — | fab | — | https://alistair.cockburn.us/hexagonal-architecture |
| primary | B3 | T2 | — † | — | cur | — | https://docs.port.io/platform-administration/security/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.port.io/api-reference/security/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.port.io/guides/all/create-cloud-resource-using-iac/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.port.io/agent-management/port-mcp-server/installation/ |
| primary | B3 | T2 | — † | — | gpt | 5.1.2 10.4.5 | https://github.com/mvp-scale/aOa |
| research | B1 | T3 | 2026-07-02 | url | kim | — | https://tianpan.co/blog/2026-07-02-ports-and-adapters-for-agents |
| research | B2 | T3 | 2026 | url | fab | U.5 | https://guiferreira.me/archive/2026/understanding-hexagonal-architecture-a-guide-to-ports-and-adapters/ |
| research | B3 | T3 | 2025-04-20 | url | kim | — | https://alistaircockburn.com/hexarch%20v1.1b%20DIFFS%2020250420-1012%20paper%2Bepub.docx.pdf |
| research | B3 | T3 | — † | — | fab | — | https://8thlight.com/insights/a-color-coded-guide-to-ports-and-adapters |
| research | B3 | T3 | — † | — | fab | — | https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/hexagonal-architecture.html |
| research | B3 | T3 | — † | — | kim | — | https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/hexagonal-architectures/hexagonal-architectures.pdf |
| research | B3 | T3 | — † | — | cur fab | cursor:U.0 | https://en.wikipedia.org/wiki/Hexagonal_architecture_(software) |
| research | B3 | T3 | — † | — | kim | — | https://foojay.io/today/ports-and-adapters-in-java-keeping-your-core-clean/ |
| research | B3 | T3 | — † | — | kim | — | https://twingital-ventures.com/en/publications/hexagonal-architecture-condition-governability/ |
| WILD | B1 | U | 2026-08-05 | age | cur fab | U.5 cursor:U.0 | https://levelup.gitconnected.com/ports-and-adapters-and-the-mess-in-the-middle-dbe1d98c7172 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.software-architecture-gathering.com/session/the-hexagonal-or-ports-adapters-architecture/ |
| WILD | B2 | U | 2026-06-05 | age | cur fab | cursor:U.0 | https://architecturediagram.ai/blog/hexagonal-architecture-diagram |
| WILD | B3 | U | — † | — | fab | — | https://blogs.pavanrangani.com/hexagonal-architecture-ports-adapters-guide/ |
| WILD | B3 | U | — † | — | kim | — | https://calmops.com/software-engineering/hexagonal-architecture-ports-adapters-pattern/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/rafaeljcamara/ports-and-adapters-hexagonal-architecture-547c |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/godofgeeks/hexagonal-architecture-ports-and-adapters-3ljb |
| WILD | B3 | U | — † | — | fab | U.4 | https://github.com/denyspoltorak/metapatterns/wiki/Hexagonal-Architecture |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/ports-and-adapters?l=javascript |
| WILD | B3 | U | — † | — | fab | — | https://inprotech.es/en/ports-adapters-hexagonal-architecture/ |
| WILD | B3 | U | — † | — | kim | — | https://keytologic.com/clean-architecture-vs-hexagonal-architecture-which-one-actually-wins-in-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://kisztof.medium.com/using-hexagonal-architecture-and-ddd-together-for-robust-software-design-d4b06a9beec3 |
| WILD | B3 | U | — † | — | fab | U.5 | https://smartcr.org/architecture/hexagonal-architecture-tutorial/ |
| WILD | B3 | U | — † | — | kim | — | https://talent500.com/blog/hexagonal-architecture-pattern-complete-guide-examples/ |
| WILD | B3 | U | — † | — | kim | — | https://tms-outsource.com/blog/posts/hexagonal-architecture/ |
| WILD | B3 | U | — † | — | kim | — | https://tutorials.dodatech.com/software-architecture/hexagonal-architecture/ |

### U.2

**Q:** If a standard exists: which version is pinned, and what conformance test proves the adapter complies?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-03 | url | fab | — | https://opcconnect.opcfoundation.org/2026/03/compliance-corner-march-2026/ |
| core | B3 | T1 | 2025-03-28 | exc | cur | — | https://usb.org/document-library/usb-type-cr-connectors-and-cable-assemblies-compliance-document-rev-21b |
| core | B3 | T1 | 2022-08-03 | url | cur | — | https://www.usb.org/sites/default/files/USB-C%20Product%20Matrix%202022%2008%2003.pdf |
| core | B3 | T1 | 2022-04-22 | exc | cur | — | https://www.usb.org/sites/default/files/USB%20PD3%20CTS%20r1.4%20V3%20OR.pdf |
| core | B3 | T1 | 2021-06 | exc | cur | — | https://usb.org/sites/default/files/USB%20Type-C_Compliance%20Document_Rev_2_1b_June_2021.pdf |
| core | B3 | T1 | 2019-08 | exc | cur | — | https://usb.org/sites/default/files/USB%20Type-C%20Spec%20R2.0%20-%20August%202019.pdf |
| core | B3 | T1 | — † | — | fab | — | https://www.cdr.gov.au/resources/guides/conformance-test-suite-version-history-and-guidance |
| core | B3 | T1 | — † | — | fab | — | https://www.odva.org/subscriptions-services/software/ |
| core | B3 | T1 | — † | — | fab | — | https://www.opengroup.org/face/conformance-testsuites |
| core | B3 | T1 | — † | — | fab | — | https://ttcn-3.etsi.org/index.php/downloads/publicts/publicts-etsi/65-publicts-its |
| core | B3 | T1 | — † | — | fab | — | https://www.usb.org/euconformity |
| primary | B2 | T2 | 2026-06-01 | exc | fab | U.10 | https://github.com/Toloka/tolokaforge/issues/18 |
| primary | B3 | T2 | — † | — | cur fab kim | 9.1 cursor:9.4.1 | https://github.com/modelcontextprotocol/conformance |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/prime-vector/open-agent-spec/blob/main/spec/conformance/PROTOCOL.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/prime-vector/open-agent-spec/blob/main/spec/conformance/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/prime-vector/open-agent-spec/blob/main/spec/open-agent-spec-1.6.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agentidentitytrustprotocol/aitp-rs/blob/main/docs/conformance.md |
| primary | B3 | T2 | — † | — | fab | — | https://iottestware.readthedocs.io/en/master/conformance_testing.html |
| primary | B3 | T2 | — † | — | kim | — | https://pypi.org/project/open-agent-spec/ |
| research | B2 | T3 | 2026-03 | url | fab | 1.1.2 9.1 | https://arxiv.org/pdf/2603.23801 |
| research | B3 | T3 | 2025-07 | url | fab | — | https://arxiv.org/pdf/2507.00378 |
| research | B3 | T3 | 2021-08 | url | fab | — | https://arxiv.org/pdf/2108.07075 |
| research | B3 | T3 | 2021-04 | url | fab | — | https://arxiv.org/pdf/2104.07460 |
| research | B3 | T3 | 2020-12 | url | fab | — | https://arxiv.org/pdf/2012.03759 |
| research | B3 | T3 | — † | — | kim | — | https://openarmature.org/capabilities/conformance-adapter/ |
| research | B3 | T3 | — † | — | kim | — | https://openarmature.org/proposals/0055-conformance-adapter-capability/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://dilithink-adaptertech.news/power-adapter-certification-emc-standards-industry-specific-requirements-2026-update/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://ucphub.ai/11-things-every-developer-needs-from-the-ucp-github-repository-in-2026/ |
| WILD | B2 | U | 2026-06 | exc | fab | — | https://standards.iteh.ai/articles/blog/road-vehicles/automotive-road-vehicle-standards-june-2026 |
| WILD | B2 | U | 2026-05-17 | exc | kim | — | https://github.com/attestplane/attestplane/blob/main/docs/adr/0014-adapter-conformance-fixture-pinning.md |
| WILD | B3 | U | — † | — | kim | — | https://github.com/LunarCommand/openarmature-python/blob/main/conformance.toml |
| WILD | B3 | U | — † | — | fab | — | https://www.valid8.com/datasheets/sip-conformance |

### U.3

**Q:** If no standard exists: what is the minimal platform-owned interface, and what is the policy for extending it?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/w3c/webextensions/issues/1041 |
| primary | B2 | T2 | 2026 | exc | fab | — | https://help.sap.com/doc/sap-api-policy/latest/en-US/API_Policy_latest.pdf |
| primary | B3 | T2 | — † | — | kim | — | https://basedapp.gitbook.io/docs/integrations/mini-apps-platform/03-host-contract.md |
| primary | B3 | T2 | — † | — | kim | — | https://basedapp.gitbook.io/docs/integrations/mini-apps-platform/06-bridge-and-codegen |
| primary | B3 | T2 | — † | — | cur | — | https://docs.zephyrproject.org/latest/kernel/drivers/index.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.zephyrproject.org/latest/develop/api/vendor_interfaces_policy.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.zephyrproject.org/latest/develop/api/design_guidelines.html |
| primary | B3 | T2 | — † | — | cur | — | https://fuchsia.dev/fuchsia-src/contribute/governance/rfcs/0241_explicit_platform_external |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/openagentprotocol-OAP/oap-spec/blob/main/rfcs/RFC-0024-schema-negotiation-and-versioning.md |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/agent-host-protocol/specification/versioning.html |
| research | B2 | T3 | 2026 | exc | fab | — | https://konghq.com/blog/engineering/api-a-rapidly-changing-landscape |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/ai_superapp/your-mini-apps-are-calling-apis-you-never-meant-to-expose-designing-the-host-communication-3b5a |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/versioning-ai-agent-tools-schema-evolution.html |
| research | B3 | T3 | — † | — | kim | — | https://palancar.net/open-web/web-extensions-api-cross-browser-compatibility/ |
| research | B3 | T3 | — † | — | kim | — | https://zuplo.com/learning-center/semantic-api-versioning |
| WILD | B2 | U | 2026 | exc | fab | — | https://community.sap.com/t5/technology-q-a/impacts-of-sap-api-policy-v4-2026-on-existing-customer-integrations/qaq-p/14381879 |
| WILD | B2 | U | 2026 | exc | fab | — | https://procurementmag.com/news/sap-api-update-2026-new-standards-for-procurement-systems |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.systemdesignhandbook.com/guides/api-design/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://tblocks.com/articles/api-trends/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.xano.com/blog/modern-api-design-best-practices/ |
| WILD | B2 | U | 2026-06 | exc | fab | — | https://www.digitalapplied.com/blog/rest-api-design-2026-engineering-reference-best-practices |
| WILD | B2 | U | 2026-04 | url | fab | — | https://www.cto.mil/wp-content/uploads/2026/04/API-Tech-Guidance-MVCR3-March2026.pdf |
| WILD | B2 | U | 2026-03 | exc | fab | — | https://buildwithfern.com/post/api-design-best-practices-guide |
| WILD | B2 | U | 2026-01 | exc | fab | — | https://treblle.com/blog/api-governance-best-practices |
| WILD | B3 | U | — † | — | fab | — | https://www.cms.gov/priorities/burden-reduction/overview/interoperability/implementation-guides-standards/application-programming-interfaces-apis-relevant-standards-implementation-guides-igs |
| WILD | B3 | U | — † | — | kim | — | https://geodocs.dev/ai-agents/agent-versioning-documentation-spec |
| WILD | B3 | U | — † | — | cur | — | https://github.com/zephyrproject-rtos/zephyr/issues/61227 |
| WILD | B3 | U | — † | — | fab | — | https://sapinsider.org/blogs/sap-api-policy-update-developers-partners/ |

### U.4

**Q:** Where does the adapter live (repo, owner), and which vendor-specific features are explicitly allowed to leak through?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://github.com/xmolecules/jmolecules-integrations/issues/306 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/nimbus/nimbus/blob/main/docs/private/architecture/runtime/adapter-boundary.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/SavinRazvan/eXo_adapters/blob/main/docs/implementing-a-runtime-adapter.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/2bTwist/baasdk |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/jambonz/llm/blob/1a0cd24b/README.md |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/articles/what-is-ai-sdk-abstraction-layer/ |
| research | B2 | T3 | 2026-06-08 | exc | gpt | — | https://nirmitee.io/blog/emr-integrations-after-mvp-scaling-hospital-onboarding/ |
| research | B2 | T3 | 2026-04-17 | url | cur | — | https://www.devleader.ca/2026/04/17/adapter-pattern-realworld-example-in-c-complete-implementation |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.20493 |
| research | B3 | T3 | — † | — | kim | — | https://www.banandre.com/blog/sdk-entities-leaking-business-layers-technical-debt |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/nizos/probity/6.1-adrs:-vendor-and-payload-design |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/multigrid/writing-an-adapter-layer-to-isolate-provider-specific-code-827 |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/gabrielanhaia/the-anti-corruption-layer-that-saves-your-next-vendor-migration-3m5i |
| research | B3 | T3 | — † | — | kim | — | https://hosseinnejati.medium.com/the-anti-corruption-layer-protecting-your-domain-from-legacy-systems-6da58fc5f462 |
| research | B3 | T3 | — † | — | fab | — | https://journal.optivem.com/p/hexagonal-architecture-ports-and-adapters |
| research | B3 | T3 | — † | — | kim | — | https://rj-cooper.co.uk/posts/anti-corruption-layers/ |
| research | B3 | T3 | — † | — | kim | — | https://rj-cooper.co.uk/posts/anti-corruption-layers-work-both-ways/ |
| research | B3 | T3 | — † | — | cur fab | U.5 | https://saadh393.github.io/blog/adapter-port-architecture-two-cases |
| research | B3 | T3 | — † | — | fab | — | https://vacationtracker.io/blog/big-bad-serverless-vendor-lock-in/ |
| research | B3 | T3 | — † | — | cur | — | https://yaqinhei.com/blog/five-layer-architecture-for-agentic-enterprise-apis |
| WILD | B2 | U | 2026 | exc | fab | — | https://instapods.com/blog/astro-hosting/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.openfort.io/blog/best-account-abstraction-providers |
| WILD | B3 | U | 2025-06 | url | fab | — | https://www.javacodegeeks.com/2025/06/hexagonal-architecture-in-practice-ports-adapters-and-real-use-cases.html |
| WILD | B3 | U | — † | — | fab | — | https://commons-os.github.io/patterns/api-abstraction-layer/ |
| WILD | B3 | U | — † | — | cur | — | https://github.com/yaalalabs/agent-kernel/blob/develop/AGENTS.md |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9177271 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8953796 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7317912 |
| WILD | B3 | U | — † | — | fab | — | https://metapatterns.io/implementation-metapatterns/hexagonal-architecture/ |
| WILD | B3 | U | — † | — | fab | — | https://thecodeforge.io/system-design/hexagonal-architecture/ |

### U.5

**Q:** Exit test: name a second implementation. Can it be swapped with zero caller changes? Has this been tried?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | 2024-12 | exc | fab | — | https://github.com/swiftlang/swift-testing/pull/858 |
| primary | B3 | T2 | — † | — | cur kim | 3.5.11 | https://docs.pact.io/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/swiftlang/swift-evolution/blob/main/proposals/testing/0008-exit-tests.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/VaishGajaraj/doppel |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/chengxilo/serify |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/nalediym/difftest |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/sekacorn/ModelSwapBench |
| primary | B3 | T2 | — † | — | fab | — | https://man7.org/linux/man-pages/man2/_exit.2.html |
| research | B1 | T3 | 2026-07-23 | exc | cur | — | https://dev.to/mads_hansen_27b33ebfee4c9/do-the-connector-exit-test-before-the-connector-demo-wins-1a5l |
| research | B3 | T3 | 2024 | url | cur | — | https://www.cs.princeton.edu/courses/archive/fall24/cos326/lec/16-module-equivalence.pdf |
| research | B3 | T3 | 2020-01 | url | cur | — | https://people.csail.mit.edu/rinard/paper/popl20.replacement.pdf |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/charleshornick/runtime-adapter-hot-swapping-with-ports-adapters-the-pattern-alistair-cockburn-didnt-document-56cg |
| WILD | B2 | U | 2026 | exc | fab | — | https://satsuite.collegeboard.org/sat/testing-staff/changes |
| WILD | B2 | U | 2026-02-26 | age | kim | — | https://github.com/orbs-network/spot/commit/f97441f9e5b8ad29c2fdb381150be5b3a305066c |
| WILD | B3 | U | 2024-04 | url | fab | — | https://lkml.rescloud.iu.edu/2404.3/01134.html |
| WILD | B3 | U | — † | — | fab | — | https://blog.alexrusin.com/future-proof-your-code-a-guide-to-ports-adapters-hexagonal-architecture/ |
| WILD | B3 | U | — † | — | kim | — | https://github.com/orbs-network/spot/blob/master/src/adapter/UniversalAdapter.sol |
| WILD | B3 | U | — † | — | kim | — | https://github.com/orbs-network/spot/blob/master/src/adapter/Settler.sol |
| WILD | B3 | U | — † | — | kim | — | https://github.com/orbs-network/spot/blob/master/test/UniversalAdapter.t.sol |
| WILD | B3 | U | — † | — | kim | — | https://github.com/orbs-network/spot/blob/master/test/Settler.t.sol |
| WILD | B3 | U | — † | — | fab | U.10 | https://ilovedotnet.org/blogs/ddd-ports-and-adapters-pattern-in-dotnet/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/wearewaes/ports-and-adapters-as-they-should-be-6aa5da8893b |
| WILD | B3 | U | — † | — | fab | — | https://www.rack2cloud.com/cloud-exit-validation/ |
| WILD | B3 | U | — † | — | kim | — | https://stackoverflow.com/questions/16237135/writing-a-single-unit-test-for-multiple-implementations-of-an-interface |
| WILD | B3 | U | — † | — | fab | — | https://synchronium.github.io/software-architecture-wiki/styles/ports-and-adapters.html |
| WILD | B3 | U | — † | — | fab | — | https://thelinuxcode.com/exit0-vs-exit1-in-cc-with-examples-practical-guidance-for-real-programs/ |
| WILD | B3 | U | — † | — | fab | — | https://thelinuxcode.com/exit-function-in-c/ |

### U.6

**Q:** Selection criteria and weights: open source, license, maturity, standard conformance, operability, community, cost.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B1 | T3 | 2026-08-27 | exc | fab | — | https://www.openhands.dev/blog/how-to-choose-open-source-llm |
| research | B3 | T3 | 2022 | url | cur | — | https://www.sciencedirect.com/science/article/pii/S0164121222000267 |
| research | B3 | T3 | 2021 | url | fab | — | https://link.springer.com/article/10.1186/s42400-021-00084-8 |
| research | B3 | T3 | 2019 | url | cur | — | https://www.scitepress.org/Papers/2019/79592/79592.pdf |
| research | B3 | T3 | 2014-12 | url | fab | — | https://arxiv.org/pdf/1412.2977 |
| research | B3 | T3 | — † | — | kim | — | https://appwrite.io/blog/post/how-to-evaluate-open-source-maturity-before-using-it-in-production |
| research | B3 | T3 | — † | — | kim | — | https://www.compelframework.org/articles/build-vs-buy-vs-integrate |
| research | B3 | T3 | — † | — | fab | — | https://dwheeler.com/oss_fs_eval.html |
| research | B3 | T3 | — † | — | kim | — | https://notionalpha.com/methodology/rubric |
| research | B3 | T3 | — † | — | cur | — | https://onlinelibrary.wiley.com/doi/10.1002/spe.2682 |
| research | B3 | T3 | — † | — | kim | — | https://ossalt.com/guides/how-to-evaluate-open-source-software-enterprise |
| research | B3 | T3 | — † | — | cur kim | 8.3.5 | http://www.qsos.org/assets/qsos-2.0_en.pdf |
| research | B3 | T3 | — † | — | fab | — | https://www.researchgate.net/publication/220542381_Evaluation_criteria_for_freeopen_source_software_products_based_on_project_analysis |
| research | B3 | T3 | — † | — | kim | — | https://rexblack.com/resources/writing/build-vs-buy-vs-assemble |
| research | B3 | T3 | — † | — | cur fab | — | https://www.timreview.ca/article/146 |
| WILD | B2 | U | 2026 | exc | fab | — | https://appreviewlab.com/open-source-software-reviews-guide-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://benchlm.ai/best/open-source |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.digitalapplied.com/blog/open-weight-model-licence-audit-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.flexsin.com/blog/what-are-the-most-sought-after-open-source-licences-in-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.sitepoint.com/opensource-vs-commercial-llms-the-complete-guide-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://vettedconsumer.com/what-open-weights-lets-you-do-the-2026-model-license-map-read-from-the-actual-texts/ |
| WILD | B3 | U | — † | — | kim | — | https://agent.nexus/blog/how-to-evaluate-open-source-ai-agents |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Business_Readiness_Rating |
| WILD | B3 | U | — † | — | kim | — | https://github.com/borghei/Claude-Skills/blob/HEAD/engineering/tech-stack-evaluator/SKILL.md |
| WILD | B3 | U | — † | — | fab | — | https://www.hexaviewtech.com/blog/evaluation-framework-weighted-scoring-model-open-source-ai-tools |
| WILD | B3 | U | — † | — | kim | — | https://www.infodivelabs.com/blog/build-vs-buy-decisions |
| WILD | B3 | U | — † | — | kim | — | https://opensources.live/how-to-evaluate-and-integrate-third-party-open-source-projec |

### U.7

**Q:** What data does this box own, in what format, and can it be exported without the tool?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://github.com/MacPaw/portable-memory-swift |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/MacPaw/portable-memory |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/wanda1416/ai-chat-exporter |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/k4Karlal/PersonaPort |
| primary | B3 | T2 | — † | — | cur | — | https://support.box.com/hc/en-us/articles/360043697134-Download-Files-and-Folders-from-Box |
| primary | B3 | T2 | — † | — | cur | — | https://support.box.com/hc/en-us/articles/360044196373-The-Basics-of-Box |
| primary | B3 | T2 | — † | — | cur | — | https://support.box.com/hc/en-us/articles/360043697494-Using-Box-Drive-Basics |
| primary | B3 | T2 | — † | — | cur | — | https://support.box.com/hc/en-us/articles/360043696314-Search-for-Files-Folders-and-Content |
| research | B2 | T3 | 2026 | exc | fab | — | https://onlinelibrary.wiley.com/doi/10.1111/jems.12643 |
| research | B3 | T3 | — † | — | kim | — | https://research.macpaw.com/publications/portable-memory |
| research | B3 | T3 | — † | — | cur | — | https://www.syscloud.com/saas-data-protection-center/box/export-box-data/ |
| research | B3 | T3 | — † | — | kim | — | https://untied.dev/how-to-build-an-exit-strategy-into-your-saas-contracts-data- |
| WILD | B2 | U | 2026 | exc | fab | — | https://jsterlinglabs.com/blog/the-2026-automation-data-portability-checklist-for-agencies |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.topetl.com/blog/most-effective-10-no-vendor-lock-in-file-pipelines |
| WILD | B2 | U | 2026-03 | url | fab | — | https://dasroot.net/posts/2026/03/data-portability-social-media-export-migration/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Data_portability |
| WILD | B3 | U | — † | — | fab | — | https://www.fast-lta.de/en/blog/vendor-lock-in-vermeiden |
| WILD | B3 | U | — † | — | fab | — | https://www.fivetran.com/learn/data-portability |
| WILD | B3 | U | — † | — | kim | — | https://www.genieai.co/en-us/blog/contract-saas-vendor-lock-in-legal-strategies-to-maintain-data-portability-and-exit-rights |
| WILD | B3 | U | — † | — | kim | — | https://www.preparebuddy.com/blog/data-ownership-exit-rights-checklist-2026/ |
| WILD | B3 | U | — † | — | kim | — | https://schemas.pub/schemas/1 |
| WILD | B3 | U | — † | — | fab | — | https://selleo.com/blog/what-is-vendor-lock-in-in-cloud-computing |
| WILD | B3 | U | — † | — | fab | — | https://www.solved.scality.com/data-portability-standards/ |
| WILD | B3 | U | — † | — | fab | — | https://stackable.tech/en/blog/how-do-you-avoid-vendor-lock-in-when-choosing-a-new-data-platform/ |
| WILD | B3 | U | — † | — | fab | — | https://www.thinkitive.com/blog/ehr-data-portability-principles/ |
| WILD | B3 | U | — † | — | kim | — | https://toslawyer.com/saas-vendor-lock-in-exit-clauses-data-portability/ |
| WILD | B3 | U | — † | — | kim | — | https://turleylaw.com/blog/saas-data-ownership-exit-strategy |

### U.8

**Q:** What does this box emit for observability and lineage, and via which contract?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07 | exc | cur kim | 6.3.5 8.4.4 | https://github.com/OpenLineage/openlineage-site/blob/main/versioned_docs/version-1.43.0/spec/object-model.md |
| core | B3 | T1 | — † | — | cur kim | 6.3.2 | https://github.com/OpenLineage/OpenLineage/ |
| core | B3 | T1 | — † | — | kim | — | https://github.com/open-telemetry/semantic-conventions/issues/3762 |
| primary | B2 | T2 | 2026 | url | fab | — | https://opentelemetry.io/blog/2026/ |
| primary | B3 | T2 | — † | — | fab | — | https://changelog.opentelemetry.io/ |
| primary | B3 | T2 | — † | — | cur | — | https://corvid-lang.org/docs/reference/core-semantics |
| primary | B3 | T2 | — † | — | cur | — | https://corvid-lang.org/docs/operations/observability-conformance |
| primary | B3 | T2 | — † | — | cur | — | https://corvid-lang.org/docs/guides/observability |
| primary | B3 | T2 | — † | — | kim | — | https://docs.cloud.google.cn/dataplex/docs/openlineage-mapping |
| primary | B3 | T2 | — † | — | kim | — | https://docs.cloud.google.com/dataplex/docs/open-lineage |
| primary | B3 | T2 | — † | — | fab gpt | 6.3.1 6.3.3 6.3.5 8.4.4 | https://github.com/OpenLineage/openlineage |
| primary | B3 | T2 | — † | — | fab | 6.3.1 6.3.4 6.3.5 8.4.4 | https://github.com/OpenLineage/OpenLineage/releases |
| primary | B3 | T2 | — † | — | fab | — | https://openlineage.io/blog/openlineage-takes-inspiration-from-opentelemetry/ |
| primary | B3 | T2 | — † | — | fab | — | https://opentelemetry.io/blog/page/2/ |
| research | B1 | T3 | 2026-08-25 | exc | kim | — | https://data-engineering-weekly.contentwave.net/article/opentelemetry-launches-datalineage-v10-spec-pipelines-must-adapt |
| research | B1 | T3 | 2026-07-25 | exc | kim | — | https://data-engineering-weekly.contentwave.net/article/openlineage-and-opentelemetry-publish-joint-lineage-otlp-spec |
| research | B3 | T3 | 2025 | url | fab | — | https://www.usenix.org/conference/srecon25emea/presentation/obuchowski |
| research | B3 | T3 | — † | — | kim | — | https://www.datadoghq.com/blog/data-lineage/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/laura_cristinachicovisd/how-to-integrate-apache-airflow-with-openlineage-for-end-to-end-traceability-15ca |
| WILD | B2 | U | 2026-05 | url | fab | 6.3.5 | https://datalakehousehub.com/blog/2026-05-openlineage-observability/ |
| WILD | B3 | U | — † | — | fab | — | https://blog.dataengineerthings.org/embracing-data-observability-with-opentelemetry-and-openlineage-4f6f13b3e20b?gi=38b38b98fe16 |
| WILD | B3 | U | — † | — | fab | 8.4.4 | https://cloudrps.com/blog/data-catalog-data-lineage-openmetadata-datahub/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Opencast_(software) |
| WILD | B3 | U | — † | — | fab | 6.3.1 6.3.4 8.4.4 | https://en.wikipedia.org/wiki/OpenSearch_(software) |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/OpenTofu |
| WILD | B3 | U | — † | — | fab | 1.1.3 | https://en.wikipedia.org/wiki/OpenAI_Codex_(AI_agent) |
| WILD | B3 | U | — † | — | cur | — | https://github.com/Micrurus-Ai/Corvid-lang/blob/main/docs/guides/observability.md |
| WILD | B3 | U | — † | — | cur | — | https://github.com/Micrurus-Ai/Corvid-lang/blob/main/crates/corvid-trace-schema/src/event.rs |
| WILD | B3 | U | — † | — | fab | — | https://www.improving.com/thoughts/effective-data-lineage-strategies-for-real-time-systems/ |
| WILD | B3 | U | — † | — | fab | — | https://openobserve.ai/blog/what-is-opentelemetry/ |
| WILD | B3 | U | — † | — | kim | — | https://www.youtube.com/watch?v=AVNzNThXn9M |

### U.9

**Q:** Built vs planned: what is the MVP scope and what is deliberately deferred?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://www.atlassian.com/agile/product-management/minimum-viable-product |
| primary | B3 | T2 | — † | — | kim | — | https://humanitec.com/blog/how-to-build-a-minimum-viable-platform-mvp |
| research | B1 | T3 | 2026-08-21 | exc | gpt | — | https://mvphub.tech/blog/what-saas-mvp-development-company-should-build-first |
| research | B2 | T3 | 2026 | exc | cur fab | — | https://www.classicinformatics.com/blog/minimum-viable-product |
| research | B2 | T3 | 2026 | url | cur | — | https://enlightlab.com/how-to-scope-an-mvp-in-2026-features-requirements/ |
| research | B2 | T3 | 2026-03-31 | exc | gpt | — | https://themvp.studio/insights/how-to-build-an-mvp |
| research | B3 | T3 | — † | — | fab kim | — | https://intersog.co.il/blog/how-to-scope-an-mvp-without-building-your-whole-product-roadmap/ |
| research | B3 | T3 | — † | — | cur | — | https://www.koragence.com/en/how-to-scope-an-mvp |
| research | B3 | T3 | — † | — | cur kim | — | https://mvpdevelopment.company/blog/mvp-scope |
| research | B3 | T3 | — † | — | kim | — | https://platformengineering.org/blog/what-is-a-minimum-viable-platform-mvp |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.chronoinnovation.com/resources/mvp-development-guide/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://grnplatform.com/blog/in-house-vs-agency-vs-ai-accelerated-team-mvp-cost-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.softermii.com/blog/for-startups/mvp-development-guide-process-costs-and-real-examples |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.techtic.com/blog/mvp-development-cost-2026-pricing-breakdown/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.valtorian.com/blog/mvp-scope-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.valtorian.com/blog/agency-mvp-process |
| WILD | B2 | U | 2026 | exc | fab | — | https://wearepresta.com/the-complete-mvp-roadmap-guide-for-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.weweb.io/blog/mvp-development-complete-guide-from-idea-to-launch |
| WILD | B2 | U | 2026-05-09 | url | kim | — | https://darketype.hashnode.dev/2026-05-09-the-backlog-is-a-feature |
| WILD | B2 | U | 2026-03-20 | exc | gpt | — | https://hashtagplus.com/release-notes |
| WILD | B3 | U | — † | — | fab | — | https://www.bolderapps.com/blog-posts/mvp-scope-planning |
| WILD | B3 | U | — † | — | fab | — | https://www.f22labs.com/blogs/mvp-milestones-deliverables/ |
| WILD | B3 | U | — † | — | kim | — | https://git.autonomic.zone/recipe-maintainers/cc-ci/commit/44e88f3750bcdbf60c60706df145601f7d20eeab |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/johanpearson/xG-Arcade/blob/main/MVP-SCOPE.md |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/gabrielleeyj/MNEME |
| WILD | B3 | U | — † | — | kim | — | https://home.turangga.workers.dev/fernando_azevedo_6844e930/prioritization-postmortem-when-the-roadmap-becomes-the-incident-4a72 |
| WILD | B3 | U | — † | — | gpt | — | https://www.houseofmvps.com/24-hour-poc-scoping |
| WILD | B3 | U | — † | — | fab | — | https://www.iotforall.com/how-to-scope-iot-app-mvp |
| WILD | B3 | U | — † | — | fab | — | https://www.netguru.com/blog/roadmap-mvp |
| WILD | B3 | U | — † | — | kim | — | https://prodmoh.com/blog/ship-block-defer-decision-queue-head-of-product |
| WILD | B3 | U | — † | — | fab | — | https://www.sigmainfo.net/blog/how-to-scope-an-mvp-what-to-include-what-to-cut-and-why/ |
| WILD | B3 | U | — † | — | kim | — | https://snowmanlabs.com/insights/reduce-engineering-backlog-without-hiring |
| WILD | B3 | U | — † | — | kim | — | https://www.youtube.com/watch?v=9JzsCPjfmyc |

### U.10

**Q:** Can a third party implement this box's port out of tree and register the adapter (8.5) with no platform core changes; is there a published conformance suite that admits it, and has an out-of-tree adapter passed it?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/kubernetes/enhancements/issues/5922 |
| core | B3 | T1 | — † | — | kim | — | https://github.com/kubernetes/enhancements/pull/5923 |
| core | B3 | T1 | — † | — | kim | — | https://network-policy-api.sigs.k8s.io/npeps/npep-137-conformance-profiles/ |
| core | B3 | T1 | — † | — | fab | — | https://openbankinguk.github.io/knowledge-base-pub/conformance-tools/functional-conformance-tool/ |
| core | B3 | T1 | — † | — | fab | — | https://registry.khronos.org/OpenXR/conformance/cts_usage.html |
| primary | B3 | T2 | 2025 | url | kim | — | https://docs.redhat.com/en/documentation/red_hat_software_certification/2025/html/red_hat_openshift_software_certification_policy_guide/assembly-specialized-certifications-for-openshift-badges_openshift-sw-cert-policy-products-managed |
| primary | B3 | T2 | 2025 | url | kim | — | https://docs.redhat.com/en/documentation/red_hat_software_certification/2025/html/red_hat_software_certification_workflow_guide/con_cni-certification_openshift-sw-cert-workflow-working-with-cloud-native-network-function |
| primary | B3 | T2 | — † | — | kim | — | https://docs.paperclip.ing/reference/adapters/creating-an-adapter/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/paperclipai/paperclip/pull/2218 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/open-rgs/open-rgs/blob/main/specs/12-adapter-cookbook.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/zernie/vigiles/blob/main/docs/authoring-an-adapter.md |
| WILD | B2 | U | 2026 | exc | fab | — | https://khimananda.com/blog/infrastructure-module-registries-explained |
| WILD | B2 | U | 2026-04-14 | age | kim | — | https://github.com/PetalCat/Nexus/commit/3da729e2651486c41b7fefb53fc2416000c85d82 |
| WILD | B3 | U | 2024-03 | url | fab | — | https://lkml.iu.edu/hypermail/linux/kernel/2403.0/07095.html |
| WILD | B3 | U | — † | — | fab | — | https://awesome-dsh-plugin.com/ |
| WILD | B3 | U | — † | — | fab | — | https://www.c-sharpcorner.com/article/ports-and-adapter-architecture |
| WILD | B3 | U | — † | — | fab | — | https://chromium.googlesource.com/chromiumos/third_party/arm-trusted-firmware/+/refs/heads/upstream_mirror/rfc/arm_gicv3_driver_v1/docs/platform-migration-guide.md |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Ada_Conformity_Assessment_Test_Suite |
| WILD | B3 | U | — † | — | fab | — | https://lib.rs/crates/traverse-cli-rs |
| WILD | B3 | U | — † | — | fab | — | https://techbuzzonline.com/software-architectureports-and-adapters-pattern-beginners-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://www.yumpu.com/en/document/view/36257541/multiple-spanning-tree-protocol-conformance-test-suite-spirent |

## 1. Invocation / Entry Points

### 1.1.1

**Q:** UI ↔ agent events via AG-UI; which version; which events are mandatory?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-09-08 | age | cur fab kim gpt | 1.1.7 5.2.1 5.3.1 cursor:9.2.4 | https://docs.ag-ui.com/concepts/events |
| primary | B1 | T2 | 2026-08-31 | exc | fab gpt | — | https://pypi.org/project/ag-ui-protocol/ |
| primary | B1 | T2 | 2026-06-24 | exc | cur fab kim gpt | cursor:9.2.2 | https://github.com/ag-ui-protocol/ag-ui/releases |
| primary | B2 | T2 | 2026-06-05 | url | kim | — | https://github.com/ag-ui-protocol/ag-ui/releases/tag/release/2026-06-05 |
| primary | B3 | T2 | — † | — | cur kim | 1.1.5 | https://docs.ag-ui.com/concepts/architecture |
| primary | B3 | T2 | — † | — | kim | — | https://docs.ag-ui.com/sdk/python/core/events |
| primary | B3 | T2 | — † | — | kim | — | https://docs.ag-ui.com/concepts/agents |
| primary | B3 | T2 | — † | — | cur kim | — | https://github.com/ag-ui-protocol/ag-ui/blob/1625e70b/docs/concepts/events.mdx |
| primary | B3 | T2 | — † | — | cur fab | cursor:9.2.1 | https://github.com/ag-ui-protocol/ag-ui |
| primary | B3 | T2 | — † | — | cur kim | cursor:9.2.4 | https://github.com/ag-ui-protocol/ag-ui/blob/main/sdks/python/ag_ui/core/events.py |
| primary | B3 | T2 | — † | — | cur | cursor:9.2.4 | https://github.com/ag-ui-protocol/ag-ui/blob/1cedb73e/docs/sdk/js/core/events.mdx |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ag-ui-protocol/ag-ui/blob/d53c4ef6/docs/sdk/js/core/events.mdx |
| primary | B3 | T2 | — † | — | gpt | 1.1.7 5.2.1 5.3.1 | https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/concepts/events.mdx |
| primary | B3 | T2 | — † | — | gpt | 5.2.1 5.3.1 | https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/sdk/js/core/events.mdx |
| research | B1 | T3 | 2026-09-03 | exc | cur kim | cursor:9.2.3 | https://aistackcurrent.com/protocols/ag-ui/ |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.21334 |
| research | B3 | T3 | — † | — | fab | — | https://aws.amazon.com/blogs/machine-learning/build-generative-ui-for-ai-agents-on-amazon-bedrock-agentcore-with-the-ag-ui-protocol/ |
| research | B3 | T3 | — † | — | cur kim | — | https://www.channel.tel/blog/ag-ui-protocol-agent-frontend-streaming |
| research | B3 | T3 | — † | — | cur | — | https://hackernoon.com/the-16-events-you-need-to-master-to-build-ag-ui-apps |
| WILD | B2 | U | 2026 | url | fab | 5.2.1 | https://anhtu.dev/ag-ui-protocol-when-ai-agents-render-ui-for-users-2026-2246 |
| WILD | B2 | U | 2026 | exc | fab | 1.1.5 5.3.1 9.1 9.2 9.3 | https://www.mindstudio.ai/blog/six-agent-protocols-ai-builders-2026 |
| WILD | B2 | U | 2026 | url | fab | 5.2.1 | https://nerova.ai/guides/what-is-ag-ui-agent-user-interaction-protocol-2026 |
| WILD | B2 | U | 2026-03-28 | exc | fab | — | https://newreleases.io/latest?start=0bhpp90 |
| WILD | B3 | U | — † | — | fab | — | https://builder.aws.com/content/3Bi9i40bG41aMJD8mDW6W0EBHLe/ag-ui-a-practical-look-at-the-agent-to-user-protocol |
| WILD | B3 | U | — † | — | fab kim | 5.2.1 5.3.1 | https://www.codecademy.com/article/ag-ui-agent-user-interaction-protocol |
| WILD | B3 | U | — † | — | fab | 5.2.1 5.3.1 9.1 9.3 | https://dev.to/jubinsoni/the-agent-protocol-stack-mcp-vs-a2a-vs-ag-ui-when-to-use-what-6dn |
| WILD | B3 | U | — † | — | fab | — | https://www.guvi.in/blog/how-the-agent-user-interaction-protocol-works/ |
| WILD | B3 | U | — † | — | fab | 1.1.7 | https://medium.com/@codewithrashid/ag-ui-the-missing-piece-of-the-ai-agent-stack-186bb15d1357 |
| WILD | B3 | U | — † | — | fab | — | https://tiarebalbi.com/en/blog/ag-ui-protocol-wire-format-kotlin-spring |

### 1.1.2

**Q:** Session contract labelled "ACP": confirm this is the Agent Client Protocol (client ↔ agent session), not the former IBM Agent Communication Protocol (since merged into A2A).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-08-29 | url | fab kim | 9.3 | https://lfaidata.foundation/communityblog/2025/08/29/acp-joins-forces-with-a2a-under-the-linux-foundations-lf-ai-data/ |
| core | B3 | T1 | — † | — | cur kim | cursor:1.1.3 cursor:9.1.3 cursor:9.2.3 | https://agentclientprotocol.com/protocol/v2/overview |
| core | B3 | T1 | — † | — | cur kim | cursor:1.1.3 cursor:9.1.3 cursor:9.2.3 | https://agentclientprotocol.com/protocol/v2/session-setup |
| core | B3 | T1 | — † | — | cur kim | 1.1.6 cursor:9.1.1 cursor:9.1.2 cursor:9.1.5 | https://agentclientprotocol.com/protocol/v2/migration |
| primary | B1 | T2 | 2026-08-20 | exc | gpt | — | https://github.com/agentclientprotocol/agent-client-protocol/blob/main/CHANGELOG.md |
| primary | B2 | T2 | 2026-04-22 | exc | fab gpt | 1.1.6 3.1.2 9.1 9.2 | https://agentclientprotocol.com/updates |
| primary | B2 | T2 | 2026-03-27 | exc | fab gpt | 3.1.2 | https://github.com/agentclientprotocol/claude-agent-acp/blob/main/CHANGELOG.md |
| primary | B3 | T2 | — † | — | cur fab kim | 3.1.2 cursor:1.1.3 cursor:9.1.1 cursor:9.1.6 | https://agentclientprotocol.com/get-started/introduction |
| primary | B3 | T2 | — † | — | kim | — | https://agentclientprotocol.com/rfds/v2/session-resume-replay |
| primary | B3 | T2 | — † | — | cur kim | cursor:9.1.1 cursor:9.1.2 | https://github.com/agentclientprotocol/agent-client-protocol |
| research | B2 | T3 | 2026 | exc | fab | 9.3 | https://getstream.io/blog/ai-agent-protocols/ |
| research | B2 | T3 | 2026-06 | exc | fab | 1.5.1 2.4.5 6.1.3 8.5.1 9.1 9.3 9.4 | https://arxiv.org/pdf/2606.31498 |
| research | B2 | T3 | 2026-02 | url | fab | 9.4 | https://arxiv.org/pdf/2602.11327 |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/html/2602.15055 |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.15055 |
| research | B3 | T3 | 2025-07 | url | fab | 1.5.1 8.5.1 | https://arxiv.org/pdf/2507.10644 |
| research | B3 | T3 | 2025-05 | url | fab | — | https://arxiv.org/pdf/2505.02279 |
| research | B3 | T3 | 2025-05-02 | url | cur fab | 1.5.2 cursor:0.1.2 | https://arxiv.org/html/2505.02279v1 |
| research | B3 | T3 | 2023-06 | url | fab | 1.5.1 2.4.5 9.3 9.4 | https://arxiv.org/pdf/2306.02781 |
| research | B3 | T3 | — † | — | kim | — | https://rywalker.com/research/acp-agent-communication-protocol |
| research | B3 | T3 | — † | — | cur fab kim | 8.5.2 cursor:9.3.3 cursor:9.4.3 | https://tyk.io/learning-center/agent-protocols-a-complete-guide-to-mcp-a2a-and-acp/ |
| WILD | B1 | U | 2026-08-19 | url | fab | — | https://www.forbes.com/sites/janakirammsv/2026/08/19/agent2agent-joins-the-agentic-ai-foundation-alongside-mcp/ |
| WILD | B2 | U | 2026-05-01 | url | fab | — | https://codex.danielvaughan.com/2026/05/01/codex-cli-agent-interoperability-protocols-mcp-acp-a2a/ |
| WILD | B3 | U | — † | — | kim | — | https://a2aprotocol.ai/blog/beeai-a2a-acp |
| WILD | B3 | U | — † | — | fab | — | https://ansezz.com/blog/mcp-vs-a2a-vs-acp/ |
| WILD | B3 | U | — † | — | fab | — | https://www.boldare.com/blog/agent-communication-protocol-acp-explained-what-it-is-and-why-it-matters/ |
| WILD | B3 | U | — † | — | fab | — | https://www.calummurray.ca/blog/intro-to-acp |
| WILD | B3 | U | — † | — | fab | — | https://crystl.dev/blog/agent-communication-protocols/ |
| WILD | B3 | U | — † | — | fab | — | https://dotsquarelab.com/resources/acp-and-a2a-united |
| WILD | B3 | U | — † | — | fab | — | https://www.ml4devs.com/what-is/acp-agent-communication-protocol/ |

### 1.1.3

**Q:** API described by OpenAPI; CLI is a thin client of the API or a separate surface?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-09-23 | url | kim | — | https://www.openapis.org/blog/2025/09/23/announcing-openapi-v3-2 |
| primary | B1 | T2 | 2026-09-07 | exc | gpt | — | https://docs.aws.amazon.com/workspaces-thin-client/latest/api/Welcome.html |
| primary | B1 | T2 | 2026-08-25 | exc | gpt | — | https://pypi.org/project/openapi-generator-cli/ |
| primary | B1 | T2 | 2026-08-24 | exc | kim | — | https://github.com/openapitools/openapi-generator |
| primary | B1 | T2 | 2026-08-06 | exc | kim | — | https://www.npmjs.com/package/@redocly/cli |
| primary | B2 | T2 | 2026-06 | exc | fab kim | — | https://buildwithfern.com/post/generate-cli-from-openapi-spec |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/OpenAPITools/openapi-generator |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/OpenAPITools/openapi-generator/releases |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/OpenAPITools/openapi-generator-cli |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/danielgtaylor/openapi-cli-generator |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/redocly/redocly-cli |
| primary | B3 | T2 | — † | — | fab | — | https://www.npmjs.com/package/@openapitools/openapi-generator-cli |
| primary | B3 | T2 | — † | — | cur | — | https://onlycli.github.io/OnlyCLI/docs/ |
| primary | B3 | T2 | — † | — | fab | — | https://openapi-generator.tech/ |
| primary | B3 | T2 | — † | — | kim | — | https://openapi-generator.tech/docs/installation/ |
| primary | B3 | T2 | — † | — | kim | — | https://redocly.com/blog/openapi-3-2 |
| research | B1 | T3 | 2026-07 | exc | fab | — | https://buildwithfern.com/post/what-is-an-api-cli-generator |
| research | B3 | T3 | — † | — | cur | — | https://github.com/EvilFreelancer/openapi-to-cli |
| research | B3 | T3 | — † | — | cur | — | https://github.com/kriptoburak/openapi-cli4ai |
| research | B3 | T3 | — † | — | cur | — | https://github.com/andreabedini/OnlyCLI |
| research | B3 | T3 | — † | — | cur | — | https://github.com/Itish2003/runtime-agent-cli |
| research | B3 | T3 | — † | — | kim | — | https://rest.sh/blog/turn-an-openapi-spec-into-a-cli-without-generating-code/ |
| WILD | B3 | U | — † | — | fab gpt | — | https://github.com/openapi/openapi-cli |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/openapi-specification?l=typescript |
| WILD | B3 | U | — † | — | kim | — | https://github.com/lucianfialho/spec2cli/tree/315090f4c5c9824fdfe990b312855fa8dc4ce13a |
| WILD | B3 | U | — † | — | kim | — | https://github.com/forattini-dev/dynamic-openapi-cli |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/openapistack/openapicmd |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/openai/openai-cli |
| WILD | B3 | U | — † | — | fab | — | https://guidebook.devops.uis.cam.ac.uk/reference/misc/openapi-client-generation/ |

### 1.1.4

**Q:** Streaming transport (SSE / WebSocket) abstracted from the UI framework?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | url | gpt | 3.5.1 3.5.8 3.5.10 | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/streamable-http.mdx |
| primary | B1 | T2 | 2026-07-27 | exc | gpt | — | https://developers.cloudflare.com/agents/model-context-protocol/protocol/transport/ |
| primary | B2 | T2 | 2026-06-03 | exc | gpt | — | https://developers.cloudflare.com/agents/runtime/communication/http-sse/ |
| primary | B2 | T2 | 2026-05-04 | exc | gpt | — | https://agentclientprotocol.com/rfds/streamable-http-websocket-transport |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/umbral-realtime/latest/umbral_realtime/index.html |
| primary | B3 | T2 | — † | — | cur kim | — | https://github.com/liveflux/liveflux |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ably/ably-ai-transport-js |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/microsoft/agent-framework/issues/6519 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/bewinxed/river.ts/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/durable-streams/durable-streams |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/atmosphere/atmosphere |
| primary | B3 | T2 | — † | — | kim | — | https://harness-ui.com/ |
| primary | B3 | T2 | — † | — | gpt | — | https://langchain-ai.github.io/agent-protocol/streaming/ |
| primary | B3 | T2 | — † | — | cur kim | — | https://liveflux.bpdm.dev/ |
| research | B1 | T3 | 2026-09-06 | exc | gpt | — | https://docs.reactiveagents.dev/guides/web-integration/ |
| research | B1 | T3 | 2026-07-09 | url | gpt | — | https://niteagent.com/blog/2026-07-09-streaming-agent-responses-production-guide/ |
| research | B2 | T3 | 2026-06 | url | fab | 3.4.1 6.1.3 9.1 9.3 9.4 9.5 | https://arxiv.org/pdf/2606.20570 |
| research | B2 | T3 | 2026-06 | url | fab | 3.1.7 10.3.7 | https://arxiv.org/pdf/2606.24937 |
| research | B3 | T3 | — † | — | cur | — | https://github.com/mesgjs/poly-transport |
| research | B3 | T3 | — † | — | cur | — | https://github.com/veksa/transport/ |
| research | B3 | T3 | — † | — | fab | — | https://websocket.org/guides/use-cases/ai-streaming/ |
| research | B3 | T3 | — † | — | fab | — | https://websocket.org/guides/websockets-and-ai/ |
| WILD | B1 | U | 2026-06-28 | age | gpt | — | https://www.reddit.com/r/AI_India/comments/1uhnhjo/published_part_5_of_our_data_explorer/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/streaming-llm-responses-sse-vs-websockets-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://doc.tokenpapa.ai/en/docs/blog/streaming-websocket-llm-guide |
| WILD | B2 | U | 2026 | url | fab | — | https://jetbi.com/blog/streaming-architecture-2026-beyond-websockets |
| WILD | B2 | U | 2026-04 | age | gpt | — | https://github.com/Kickflip73/agent-communication-protocol/blob/main/spec/core-v1.0.md |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/pockit_tools/the-complete-guide-to-streaming-llm-responses-in-web-applications-from-sse-to-real-time-ui-3534 |
| WILD | B3 | U | — † | — | kim | — | https://github.com/highperapp/realtime |
| WILD | B3 | U | — † | — | kim | — | https://github.com/coregx/stream |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9794304 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10148705 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10686850 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9459936 |
| WILD | B3 | U | — † | — | kim | — | https://jsr.io/@parsrun/realtime/doc/all_symbols |
| WILD | B3 | U | — † | — | fab | — | https://ridewithvia.com/resources/agent-user-interaction-protocol-when-the-frontend-got-an-ai-protocol |

### 1.1.5

**Q:** Can a third-party client use the same contracts with no platform changes?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.ag2.ai/docs/user-guide/ag-ui/backend-deepdive/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.agno.com/agent-os/interfaces/ag-ui/introduction |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/getting-started |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/security-considerations |
| research | B1 | T3 | 2026-08-12 | exc | cur | — | https://faq.apievangelist.com/questions/should-i-turn-my-openapi-into-an-mcp-server/ |
| research | B2 | T3 | 2026 | url | cur | — | https://www.stanza.dev/compare/mcp-vs-openapi |
| research | B3 | T3 | — † | — | cur | — | https://blckalpaca.at/en/knowledge-base/ai-agents/model-context-protocol-mcp/mcp-vs-openapi-tool-use |
| research | B3 | T3 | — † | — | kim | — | https://www.copilotkit.ai/blog/ag-ui-protocol-bridging-agents-to-any-front-end |
| research | B3 | T3 | — † | — | cur | — | https://dreaming.press/posts/mcp-vs-rest-api-for-agents.html |
| research | B3 | T3 | — † | — | kim | — | https://github.laiyagushi.com/namanrajpal/acp-to-agui |
| research | B3 | T3 | — † | — | kim | — | https://hackernoon.com/a-formal-analysis-of-agentic-ai-protocols-a2a-acp-and-agui |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/@balajibal/the-revolution-was-not-televised-is-acp-the-most-underestimated-protocol-of-recent-times-a3a89c337222 |
| research | B3 | T3 | — † | — | cur | — | https://viasocket.com/blog/how-ai-agents-connect-to-external-tools |
| WILD | B1 | U | 2026-07-28 | exc | fab | 3.5.10 9.4 | https://www.bovo-digital.tech/en/blog/mcp-2026-specification-stateless-enterprise-agents |
| WILD | B2 | U | 2026 | exc | fab | 5.3.1 8.5.2 9.2 9.4 | https://aasherkamal.com/resources/ai-agent-protocols-2026 |
| WILD | B2 | U | 2026 | url | fab | 2.1.2 5.3.1 | https://aigrowthagent.co/articles/a2a-protocol-explained-2026/ |
| WILD | B2 | U | 2026 | exc | fab | 9.1 9.3 | https://blog.agentailor.com/posts/top-ai-agent-protocols-2026 |
| WILD | B2 | U | 2026 | exc | fab | 9.2 9.3 9.4 | https://dev.to/alexmercedcoder/the-state-of-agentic-ai-standards-in-2026-mcp-a2a-webmcp-osi-and-the-protocol-stack-taking-3o2l |
| WILD | B2 | U | 2026 | exc | fab | 5.3.1 9.1 9.3 9.4 | https://medium.com/@visrow/a2a-mcp-ag-ui-a2ui-the-essential-2026-ai-agent-protocol-stack-ee0e65a672ef |
| WILD | B2 | U | 2026 | exc | fab | 9.3 | https://pickaxe.co/post/mcp-vs-a2a-protocol |
| WILD | B2 | U | 2026 | url | fab | 8.5.2 | https://www.ruh.ai/blogs/ai-agent-protocols-2026-complete-guide |
| WILD | B2 | U | 2026-03-26 | url | fab | 8.5.2 9.2 9.5 | https://zylos.ai/research/2026-03-26-agent-interoperability-protocols-mcp-a2a-acp-convergence/ |
| WILD | B2 | U | 2026-02-15 | url | fab | — | https://zylos.ai/research/2026-02-15-agent-to-agent-communication-protocols/ |
| WILD | B2 | U | 2026-01-12 | url | fab | — | https://zylos.ai/research/2026-01-12-multi-agent-communication/ |
| WILD | B3 | U | — † | — | fab | — | https://onereach.ai/blog/power-of-multi-agent-ai-open-protocols/ |

### 1.1.6

**Q:** ACP session lifecycle (session/new, prompt, cancel) and mid-session permission requests: does the harness (3.1) implement the agent side, and do permission requests route through policy (2.2) or straight to the UI?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-20 | exc | cur kim | cursor:9.1.1 cursor:9.1.2 | https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/announcements/acp-v2-draft.mdx |
| primary | B2 | T2 | 2026-03-27 | exc | gpt | 3.1.2 9.1 9.2 | https://agentclientprotocol.com/rfds/updates |
| primary | B2 | T2 | 2026-03-09 | exc | gpt | 3.1.2 | https://agentclientprotocol.com/announcements/session-info-update-stabilized |
| primary | B2 | T2 | 2026-03-09 | exc | gpt | 3.1.2 | https://agentclientprotocol.com/announcements/session-list-stabilized |
| primary | B3 | T2 | — † | — | cur kim | cursor:1.1.6 | https://agentclientprotocol.com/protocol/v1/tool-calls |
| primary | B3 | T2 | — † | — | cur kim | cursor:1.1.6 | https://agentclientprotocol.com/protocol/v2/prompt-lifecycle |
| primary | B3 | T2 | — † | — | fab | — | https://agentclientprotocol.com/protocol/v1/schema |
| primary | B3 | T2 | — † | — | kim | — | https://agentclientprotocol.com/rfds/v2/prompt |
| primary | B3 | T2 | — † | — | kim | — | https://agentclientprotocol.github.io/typescript-sdk/types/RequestPermissionRequest.html |
| primary | B3 | T2 | — † | — | gpt | — | https://agentclientprotocol.github.io/typescript-sdk/classes/ClientSideConnection.html |
| primary | B3 | T2 | — † | — | kim | — | https://cursor.com/docs/cli/acp |
| primary | B3 | T2 | — † | — | fab | — | https://docs.rs/agent-client-protocol/latest/agent_client_protocol/trait.Client.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.rs/agent-client-protocol |
| primary | B3 | T2 | — † | — | fab | 3.1.2 | https://github.com/earendil-works/pi/discussions/4444 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/zed-industries/agent-client-protocol/blob/4f589532/docs/protocol/tool-calls.mdx |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/google-gemini/gemini-cli/blob/2139b121/packages/cli/src/acp/acpSession.ts |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/agentclientprotocol/rust-sdk/blob/main/md/protocol-v2-quickstart.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/protocol/v2/overview.mdx |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/agentclientprotocol/agent-client-protocol/blob/main/docs/protocol/v1/overview.mdx |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/agentclientprotocol/agent-client-protocol/blob/main/schema/v1/schema.json |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.danilchenko.dev/posts/agent-client-protocol/ |
| WILD | B2 | U | 2026-03 | exc | cur fab | 3.1.2 cursor:9.1.6 | https://www.morphllm.com/agent-client-protocol |
| WILD | B3 | U | — † | — | fab | — | https://agentic-ai.readthedocs.io/en/latest/Standards/agent-client-protocol/ |
| WILD | B3 | U | — † | — | fab | — | https://deepwiki.com/zed-industries/agent-client-protocol/2.4-prompt-processing |
| WILD | B3 | U | — † | — | fab | — | https://deepwiki.com/tiru-r/pi-agent-go/3-agent-client-protocol-(acp)-and-zed-integration |
| WILD | B3 | U | — † | — | fab | — | https://deepwiki.com/zed-industries/zed/8.2-acp-protocol-and-connection |
| WILD | B3 | U | — † | — | fab | — | https://github.com/NousResearch/hermes-agent/issues/569 |
| WILD | B3 | U | — † | — | gpt | — | https://kanonak.org/acp/1.0.0/agent-client-protocol |
| WILD | B3 | U | — † | — | fab | — | https://qubittool.com/blog/agent-client-protocol-acp-guide |
| WILD | B3 | U | — † | — | fab | — | https://rywalker.com/research/zed-agent-client-protocol |

### 1.1.7

**Q:** AG-UI shared state (STATE_SNAPSHOT / STATE_DELTA) and generative UI: is state bidirectional between UI and agent, and are agent-emitted UI components sandboxed / allowlisted, or arbitrary?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur gpt | cursor:9.2.1 | https://docs.ag-ui.com/introduction |
| primary | B1 | T2 | 2026-08 | age | gpt | — | https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/state-management |
| primary | B1 | T2 | 2026-07 | age | gpt | — | https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/state-management |
| primary | B2 | T2 | 2026 | url | fab | — | https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026 |
| primary | B3 | T2 | — † | — | kim | — | https://www.assistant-ui.com/docs/tools/generative-ui |
| primary | B3 | T2 | — † | — | fab | — | https://www.copilotkit.ai/ag-ui-and-a2ui |
| primary | B3 | T2 | — † | — | fab | — | https://www.copilotkit.ai/blog/generative-ui-explained-how-agents-now-ship-their-own-interfaces |
| primary | B3 | T2 | — † | — | fab | — | https://www.copilotkit.ai/generative-ui |
| primary | B3 | T2 | — † | — | fab | — | https://www.copilotkit.ai/generative-ui-spectrum |
| primary | B3 | T2 | — † | — | fab kim gpt | — | https://docs.ag-ui.com/concepts/state |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.ag-ui.com/concepts/generative-ui-specs |
| primary | B3 | T2 | — † | — | fab | — | https://docs.copilotkit.ai/concepts/generative-ui-overview |
| primary | B3 | T2 | — † | — | kim | — | https://docs.showcase.copilotkit.ai/ag-ui/concepts/state |
| primary | B3 | T2 | — † | — | fab kim | — | https://github.com/CopilotKit/generative-ui |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/ag-ui-protocol/ag-ui/issues/2091 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/copilotkit/copilotkit |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ag-ui-protocol/ag-ui/blob/d53c4ef6/docs/concepts/state.mdx |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/assistant-ui/skills/blob/HEAD/assistant-ui/skills/tools/references/generative-ui.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/introduction.mdx |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/ag-ui-protocol/ag-ui/blob/main/docs/concepts/state.mdx |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/ |
| primary | B3 | T2 | — † | — | fab | 5.2.1 | https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/ |
| research | B3 | T3 | — † | — | kim | — | https://malakavenu.com/articles/a2ui-protocol-generative-ui |
| research | B3 | T3 | — † | — | kim | — | https://tanhdev.com/series/generative-ui-architecture/part-4-security-a11y/ |
| research | B3 | T3 | — † | — | gpt | — | https://threadplane.ai/docs/ag-ui/guides/json-render |
| research | B3 | T3 | — † | — | kim | — | https://vpodk.com/a-better-approach-to-generative-ui/ |
| WILD | B2 | U | 2026-05-01 | url | fab | — | https://earezki.com/ai-news/2026-05-01-a-coding-deep-dive-into-agentic-ui-generative-ui-state-synchronization-and-interrupt-driven-approval-flows/ |
| WILD | B2 | U | 2026-04-30 | url | fab | 5.2.1 | https://www.marktechpost.com/2026/04/30/a-coding-deep-dive-into-agentic-ui-generative-ui-state-synchronization-and-interrupt-driven-approval-flows/ |
| WILD | B3 | U | — † | — | fab | — | https://deepwiki.com/ag-ui-protocol/docs/2.4-state-management |
| WILD | B3 | U | — † | — | fab | — | https://deepwiki.com/CopilotKit/CopilotKit/6-ag-ui-protocol |
| WILD | B3 | U | — † | — | fab | — | https://github.com/AltairaLabs/Omnia/issues/614 |
| WILD | B3 | U | — † | — | kim | — | https://www.youtube.com/watch?v=UsMDkEsR-ok&vl=en-US |

### 1.2.1

**Q:** Schedule representation (cron string, ISO 8601 recurrence) and timezone rule.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://datatracker.ietf.org/doc/html/rfc5545 |
| core | B3 | T1 | — † | — | cur kim | — | https://github.com/open-source-cron/ocps/blob/main/specifications/OCPS-1.0.md |
| core | B3 | T1 | — † | — | fab | — | https://help.iso.org/en/articles/376284-iso-8601-international-standard-for-date-and-time-format |
| core | B3 | T1 | — † | — | cur | — | https://icalendar.org/iCalendar-RFC-5545/3-8-5-3-recurrence-rule.html |
| core | B3 | T1 | — † | — | cur fab | — | https://iso8601.com/ |
| primary | B3 | T2 | — † | — | cur fab | — | https://docs.prefect.io/v3/concepts/schedules |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/lingshu-cron/latest/lingshu_cron/schedule/index.html |
| primary | B3 | T2 | — † | — | kim | — | https://ex-tempo.hexdocs.pm/Tempo.Cron.html |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/javascript/api/@azure/arm-machinelearning/triggerbase |
| primary | B3 | T2 | — † | — | kim | — | https://www.php.net/manual/en/dateperiod.createfromiso8601string.php |
| research | B2 | T3 | 2026-02-09 | age | fab | — | https://oneuptime.com/blog/post/2026-02-09-cronjob-timezone-scheduling/view |
| research | B3 | T3 | 2025 | url | fab | — | https://cronmonitor.app/blog/handling-timezone-issues-in-cron-jobs |
| research | B3 | T3 | 2025 | url | fab | — | https://dev.to/cronmonitor/handling-timezone-issues-in-cron-jobs-2025-guide-52ii |
| WILD | B3 | U | — † | — | fab | — | https://cronbase.dev/guides/cron-timezone-guide |
| WILD | B3 | U | — † | — | fab | — | https://dev-brains-ai.com/blog/cron-expression-timezone-handling-guide |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/ISO_8601 |
| WILD | B3 | U | — † | — | kim | — | https://hex.pm/packages/ex_tempo/0.16.0/files/CHANGELOG.md |
| WILD | B3 | U | — † | — | fab | — | https://inventivehq.com/blog/how-do-i-handle-time-zones-daylight-saving-time-cron |
| WILD | B3 | U | — † | — | fab | — | https://timemath.net/iso-8601-converter/ |
| WILD | B3 | U | — † | — | fab | — | https://timeykit.com/learn/iso-8601-guide/ |

### 1.2.2

**Q:** Misfire, overlap and catch-up semantics defined?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-06-23 | url | kim | — | https://cadenceworkflow.io/blog/2026/06/23/cadence-schedules |
| primary | B3 | T2 | — † | — | fab kim | — | https://cadenceworkflow.io/docs/concepts/schedules |
| primary | B3 | T2 | — † | — | kim | — | https://cadenceworkflow.io/docs/go-client/schedules |
| primary | B3 | T2 | — † | — | cur fab kim | 2.4.4 | https://docs.temporal.io/schedule |
| primary | B3 | T2 | — † | — | cur | — | https://docs.temporal.io/cli/command-reference/schedule |
| primary | B3 | T2 | — † | — | kim | — | https://docs.temporal.io/troubleshooting/schedule-missed-actions |
| primary | B3 | T2 | — † | — | cur kim | — | https://github.com/cadence-workflow/Cadence-Docs/blob/master/docs/03-concepts/16-schedules.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/temporalio/temporal/blob/main/docs/architecture/schedules.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/cadence-workflow/cadence/pull/8244 |
| primary | B3 | T2 | — † | — | cur | — | https://python.temporal.io/temporalio.client.ScheduleOverlapPolicy.html |
| primary | B3 | T2 | — † | — | fab kim | — | https://www.quartz-scheduler.net/documentation/troubleshooting.html |
| primary | B3 | T2 | — † | — | kim | — | https://typescript.temporal.io/api/interfaces/client.ScheduleOptions |
| research | B2 | T3 | 2026 | url | fab | — | https://www.back4app.com/glossary/scheduled-cloud-code-cron-jobs/ |
| research | B3 | T3 | 2025 | url | fab | — | https://github.com/anthropics/claude-code/issues/60144 |
| research | B3 | T3 | — † | — | fab | — | https://androidexperto.com/quartz-scheduler-misfire-instructions-explained/ |
| research | B3 | T3 | — † | — | fab | — | https://boldsign.com/blogs/advanced-job-scheduling-quartz-net-guide/ |
| research | B3 | T3 | — † | — | fab | — | https://freedom251.com/quartz-scheduler-misfire-instructions-explained/ |
| WILD | B3 | U | — † | — | fab | — | https://cronuru.com/guides/apscheduler |
| WILD | B3 | U | — † | — | kim | — | https://deepwiki.com/quartz-scheduler/quartz/2.5.4-misfire-handling |
| WILD | B3 | U | — † | — | fab | — | https://steadycron.com/blog/dotnet-job-schedulers-compared/ |

### 1.2.3

**Q:** Dedicated scheduler vs Kubernetes CronJob vs engine-native — selection rule.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2025-12-18 | exc | cur | — | https://kubernetes.io/blog/2025/12/18/kubernetes-v1-35-job-managedby-for-jobs-goes-ga/ |
| core | B3 | T1 | — † | — | cur | — | https://www.kubernetes.dev/resources/keps/4368/ |
| core | B3 | T1 | — † | — | cur | — | https://kubernetes.io/docs/reference/kubernetes-api/batch/job-v1/ |
| core | B3 | T1 | — † | — | cur | — | https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/ |
| primary | B3 | T2 | — † | — | kim | — | https://temporal.io/blog/temporal-schedules-reliable-scalable-and-more-flexible-than-cron-jobs |
| primary | B3 | T2 | — † | — | kim | 2.4.4 | https://temporal.io/blog/how-to-convert-your-job-scheduling-system-to-temporal-schedules |
| research | B2 | T3 | 2026-05-31 | exc | fab | — | https://nivelepsilon.com/2026/05/31/why-kubernetes-struggles-with-scheduled-workloads/ |
| research | B2 | T3 | 2026-02-09 | url | cur | — | https://oneuptime.com/blog/post/2026-02-09-managedby-cronjobs-external-controller/view |
| research | B3 | T3 | 2025 | url | fab | — | https://kestra.io/resources/infrastructure/cron-replacement |
| research | B3 | T3 | 2025-08-09 | exc | kim | — | https://medium.com/@rrbadam/from-cron-to-temporal-finding-the-right-scheduler-for-the-job-a056a8d94e80 |
| research | B3 | T3 | — † | — | kim | — | https://codemia.io/archive/infra-cron-vs-app-scheduler |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/137foundry/job-queue-vs-message-queue-vs-task-scheduler-the-difference-that-actually-matters-4lp5 |
| research | B3 | T3 | — † | — | fab | — | https://discuss.kubernetes.io/t/kubernetes-cronjob-vs-spring-boot-quartz/18759 |
| research | B3 | T3 | — † | — | fab | — | https://www.flexera.com/blog/finops/kubernetes-cronjobs-the-basics-and-a-quick-tutorial/ |
| research | B3 | T3 | — † | — | fab | — | https://www.geeksforgeeks.org/devops/kubernetes-jobs-and-cronjobs-for-scheduled-tasks/ |
| research | B3 | T3 | — † | — | fab | — | https://www.golinuxcloud.com/kubernetes-cron-job-scheduler/ |
| research | B3 | T3 | — † | — | fab | — | https://www.groundcover.com/learn/kubernetes/kubernetes-cronjob |
| research | B3 | T3 | — † | — | kim | 2.4.4 | https://keithtenzer.com/temporal/Temporal_Schedules_Design_Guidance/ |
| research | B3 | T3 | — † | — | kim | — | https://kindatechnical.com/system-design-interview/cron-at-scale-temporal-airflow-and-custom-schedulers.html |
| research | B3 | T3 | — † | — | fab | — | https://medium.com/@rudra910203/kubernetes-cronjobs-vs-github-actions-scheduled-jobs-which-wastes-more-money-73d904e1ccb2 |
| research | B3 | T3 | — † | — | fab | — | https://www.redwood.com/article/kubernetes-job-scheduling/ |
| research | B3 | T3 | — † | — | kim | — | https://simpleq.io/blog/queue-vs-workflow-engine-what-startups-actually-need |
| research | B3 | T3 | — † | — | fab | — | https://smatechnologies.com/blog/replace-kubernetes-cronjob-scheduler |
| research | B3 | T3 | — † | — | kim | — | https://systhoughts.com/posts/durable-workflows-for-architects |
| research | B3 | T3 | — † | — | fab | — | https://www.techtarget.com/searchitoperations/tip/An-IT-ops-guide-to-Kubernetes-Job-vs-CronJob |
| WILD | B2 | U | 2026 | url | fab | — | https://cloudray.io/articles/cron-job-alternative |
| WILD | B3 | U | — † | — | fab | — | https://bundler.rubygems.org/gems/cron-kubernetes/versions/0.1.0 |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/kubernetes-cronjob |

### 1.3.1

**Q:** Event envelope: CloudEvents? Schema registry and AsyncAPI description?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-11 | exc | cur kim | — | https://github.com/cloudevents/spec/pull/1349 |
| core | B3 | T1 | — † | — | kim | — | https://www.asyncapi.com/docs/reference/specification/latest |
| core | B3 | T1 | — † | — | gpt | — | https://www.asyncapi.com/docs/reference/specification/v3.0.0 |
| core | B3 | T1 | — † | — | fab kim gpt | 10.2.2 | https://github.com/cloudevents/spec |
| core | B3 | T1 | — † | — | kim | — | https://github.com/cloudevents/spec/blob/ce@stable/cloudevents/spec.md |
| core | B3 | T1 | — † | — | kim | — | https://github.com/cloudevents/spec/issues/1276 |
| core | B3 | T1 | — † | — | kim | — | https://github.com/asyncapi/spec-json-schemas/issues/623 |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/asyncapi/spec |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md?plain=1 |
| core | B3 | T1 | — † | — | fab | — | https://standards.apievangelist.com/store/cloudevents/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.confluent.io/cloud/current/stream-governance/async-api.md |
| research | B3 | T3 | — † | — | fab | — | https://www.asyncapi.com/blog/asyncapi-cloud-events |
| research | B3 | T3 | — † | — | fab | — | https://www.asyncapi.com/blog/async_standards_compare |
| research | B3 | T3 | — † | — | cur kim | — | https://atamel.dev/posts/2023/05-23_asyncapi_cloudevents/ |
| research | B3 | T3 | — † | — | cur fab | — | https://developers.redhat.com/articles/2021/06/02/simulating-cloudevents-asyncapi-and-microcks |
| research | B3 | T3 | — † | — | fab | — | https://kanywst.github.io/cncf-atlas/tools/cloudevents/ |
| research | B3 | T3 | — † | — | cur fab kim | — | https://microcks.io/blog/simulating-cloudevents-with-asyncapi/ |
| research | B3 | T3 | — † | — | fab | — | https://solace.com/blog/asyncapi-cloudevents-opentelemetry-event-driven-specs-devops/ |
| WILD | B2 | U | 2026-06 | age | gpt | — | https://github.com/api-evangelist/cloudevents/blob/main/apis.yml |
| WILD | B2 | U | 2026-05-19 | exc | gpt | — | https://github.com/api-evangelist/cloudevents |
| WILD | B3 | U | 2025-04-03 | exc | kim | — | https://github.com/Lazzaretti/asyncapi-with-cloudevents-traits |
| WILD | B3 | U | — † | — | fab gpt | — | https://apis.io/apis/cloudevents/cloudevents-spec/ |
| WILD | B3 | U | — † | — | fab | — | https://cloudrps.com/blog/asyncapi-event-driven-api-specification-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/SAP/cloudevents-asyncapi-converter |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/api-evangelist/cloudevents/blob/main/json-schema/cloudevents-event-schema.json |

### 1.3.2

**Q:** Bus port (publish / subscribe / ack) independent of the adapter (NATS, Kafka, Redis Streams)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBus.html |
| core | B3 | T1 | — † | — | cur | — | https://learn.microsoft.com/en-us/azure/architecture/patterns/publisher-subscriber |
| primary | B2 | T2 | 2026-03 | age | gpt | — | https://github.com/nats-io/nats-architecture-and-design/blob/main/adr/ADR-59.md |
| primary | B2 | T2 | 2026-03-20 | exc | gpt | — | https://redis.io/tutorials/howtos/solutions/microservices/interservice-communication/ |
| primary | B3 | T2 | — † | — | cur | — | https://bus.node-ts.com/guide/transports/creating-a-transport |
| primary | B3 | T2 | — † | — | fab | — | https://docs.dapr.io/developing-applications/building-blocks/pubsub/pubsub-overview/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/tonin-core/latest/src/tonin_core/traits/event_bus.rs.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/crate/strev/latest |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Rushit/tonin/blob/main/docs/09-event-bus.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/guiaramos/strev |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/zannis/shove/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/rbaliyan/event |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/nats-io/nats-kafka |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/nats-io/nats.docs/blob/master/nats-concepts/jetstream/streams.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/nats-io/nats-site/blob/main/data/addons.toml |
| primary | B3 | T2 | — † | — | gpt | — | https://nats-io.github.io/nats.net/documentation/jetstream/publish.html |
| primary | B3 | T2 | — † | — | gpt | — | https://nats-io.github.io/nats-connector-redis/io/nats/connector/plugins/redis/RedisPubSubPlugin.html |
| primary | B3 | T2 | — † | — | gpt | — | https://pkg.go.dev/github.com/nats-io/nats-kafka |
| primary | B3 | T2 | — † | — | kim | — | https://redelay.com/docs/concepts/transports |
| primary | B3 | T2 | — † | — | cur | — | https://symfony.com/doc/current/messenger/custom-transport.html |
| research | B2 | T3 | 2026 | url | fab | 10.3.3 | https://dev.to/young_gao/real-time-event-streaming-kafka-vs-redis-streams-vs-nats-in-2026-34o1 |
| research | B2 | T3 | 2026 | url | fab | — | https://dev.to/young_gao/pubsub-messaging-patterns-redis-nats-and-when-to-use-what-2el2 |
| research | B2 | T3 | 2026-03 | url | fab gpt | — | https://www.javacodegeeks.com/2026/03/nats-vs-kafka-vs-redis-streams-for-java-microservices-when-simpler-actually-wins.html |
| research | B2 | T3 | 2026-01-21 | age | fab | — | https://oneuptime.com/blog/post/2026-01-21-redis-event-driven-microservices/view |
| research | B3 | T3 | — † | — | cur | — | https://github.com/quilla-kit/quilla-be-kit/blob/main/packages/messaging/README.md |
| WILD | B1 | U | 2026-07 | url | fab | — | https://medium.com/@m.akhan0616/no-service-ever-called-another-an-event-bus-with-nats-streaming-abfe71dd8317 |
| WILD | B2 | U | 2026 | url | fab | 10.3.3 | https://zeonedge.com/blog/event-driven-architecture-2026-kafka-nats-reactive-microservices |
| WILD | B3 | U | — † | — | fab | — | https://anykeyh.hashnode.dev/designing-event-bus-using-redis-stream |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@shivani2287/azure-service-bus-queue-topic-event-hub-vs-rabbitmq-vs-kafka-vs-redis-a-deep-dive-for-fe18800a5ec3 |

### 1.3.3

**Q:** Do scheduled triggers (1.2) emit internal events rather than dispatch directly?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | 2.4.4 | https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/event-scheduling.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.workato.com/recipes/triggers.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/seldonframe/seldonframe/blob/main/tasks/step-5-scheduled-triggers-audit.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Dhi13man/event-trigger-platform |
| research | B2 | T3 | 2026 | url | fab | — | https://alejandrorioja.com/event-triggered-vs-scheduled-agents-which-pattern-for-which-job/ |
| research | B3 | T3 | — † | — | kim | — | https://123ofai.com/articles/blocks/event-trigger |
| research | B3 | T3 | — † | — | fab | — | https://www.astronomer.io/docs/learn/airflow-event-driven-scheduling |
| research | B3 | T3 | — † | — | kim | — | https://aws.amazon.com/blogs/architecture/serverless-scheduling-with-amazon-eventbridge-aws-lambda-and-amazon-dynamodb/ |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/@systemdesignwithsage/why-we-replaced-polling-with-event-triggers-234ecda134b2 |
| research | B3 | T3 | — † | — | kim | — | https://www.nilus.be/blog/distributed_cron_patterns_in_microservices/ |
| research | B3 | T3 | — † | — | kim | — | https://www.systemdesignhandbook.com/guides/design-a-distributed-job-scheduler/ |
| research | B3 | T3 | — † | — | kim | 2.4.4 | https://www.weblineglobal.com/blog/aws-eventbridge-alternative-rabbitmq-temporal/ |
| WILD | B3 | U | 2025-10-16 | url | kim | — | https://22.frenchintelligence.org/2025/10/16/from-chaos-to-chronos-building-a-centralized-task-scheduler-for-65-microservices/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9865024 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9060100 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7882501 |
| WILD | B3 | U | — † | — | kim | — | https://letsbuildsolutions.com/blog/system-design/distributed-cron-jobs-at-scale/ |
| WILD | B3 | U | — † | — | fab | — | https://www.linkedin.com/pulse/tip-event-based-vs-schedule-based-triggers-potential-issues-truong |
| WILD | B3 | U | — † | — | fab | — | https://www2.strategy.com/producthelp/Current/SystemAdmin/WebHelp/Lang_1033/Content/About_events_and_event_triggered_schedules.htm |

### 1.3.4

**Q:** Ordering, partitioning and delivery guarantees per event type.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B2 | T2 | 2026-03-27 | url | gpt | 1.4.3 | https://pkg.go.dev/github.com/yylego/rc-yile-dispatch%40v0.0.0-20260327155956-247e7d38076d |
| primary | B3 | T2 | — † | — | fab | — | https://kafka.apache.org/33/streams/core-concepts/ |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/azure/event-hubs/event-hubs-features |
| research | B2 | T3 | 2026-02-07 | url | kim | — | https://sohilladhani.com/blog/post/2026-02-07-ordering-guarantees-in-event-driven-systems/ |
| research | B2 | T3 | 2026-01-30 | url | kim | — | https://oneuptime.com/blog/post/2026-01-30-event-ordering-guarantees/view |
| research | B2 | T3 | 2026-01-24 | url | kim | — | https://oneuptime.com/blog/post/2026-01-24-handle-message-ordering-kafka-partitions/view |
| research | B3 | T3 | 2025 | url | fab | — | https://www.growin.com/blog/event-driven-architecture-scale-systems-2025/ |
| research | B3 | T3 | 2025-06-10 | url | kim | — | https://shayne007.github.io/2025/06/10/Kafka-Message-Ordering-Theory-Practice-and-Interview-Insights/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2208.09827 |
| research | B3 | T3 | — † | — | kim | — | https://www.baeldung.com/kafka-message-delivery-multiple-partitions |
| research | B3 | T3 | — † | — | fab | — | https://www.conduktor.io/glossary/outbox-pattern-for-reliable-event-publishing |
| research | B3 | T3 | — † | — | kim | — | https://www.conduktor.io/kafka/producer-default-partitioner-and-sticky-partitioner |
| research | B3 | T3 | — † | — | fab | — | https://developer.confluent.io/patterns/event-stream/partitioned-parallelism/ |
| research | B3 | T3 | — † | — | cur | — | https://github.com/aws-samples/eda-on-aws/blob/main/docs/02-concepts/02-ordering/index.mdx |
| research | B3 | T3 | — † | — | cur | — | https://www.nilus.be/blog/message_ordering_guarantees_in_event-driven_architecture/ |
| research | B3 | T3 | — † | — | kim | — | https://pulse.support/kb/kafka-ordering-guarantees |
| research | B3 | T3 | — † | — | cur | — | https://softwarepatternslexicon.com/event-driven-architecture-patterns/ordering-and-time/partition-keys-per-stream-ordering/ |
| research | B3 | T3 | — † | — | cur kim | — | https://vetoralabs.com/system-design/concepts/messaging/ordering-guarantees |
| WILD | B3 | U | — † | — | kim | — | https://adhdecode.com/api-architecture/event-driven-and-reactive-apis/event-ordering-partitioning/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9972103 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10217256 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9672082 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6662206 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9886486 |
| WILD | B3 | U | — † | — | cur | — | https://medium.com/@sohail_saifii/the-kafka-partition-strategy-that-guarantees-message-ordering-3abe46dc6837 |

### 1.3.5

**Q:** Event versioning and consumer compatibility policy.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://www.confluent.io/blog/best-practices-for-confluent-schema-registry/ |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.confluent.io/cloud/current/sr/fundamentals/schema-evolution.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.confluent.io/platform/7.6/schema-registry/fundamentals/schema-evolution.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.solace.com/Schema-Registry/schema-registry-best-practices.htm |
| research | B2 | T3 | 2026-04 | exc | fab | — | https://medium.com/@tuananhbk1996/techniques-to-handle-versioning-in-event-driven-systems-585faa442dce |
| research | B2 | T3 | 2026-03 | url | kim | — | https://ijcsmc.com/docs/papers/March2026/V15I3202652.pdf |
| research | B2 | T3 | 2026-01-30 | age | fab | — | https://oneuptime.com/blog/post/2026-01-30-event-driven-versioning-strategies/view |
| research | B2 | T3 | 2026-01-21 | age | fab | — | https://oneuptime.com/blog/post/2026-01-21-kafka-event-versioning/view |
| research | B3 | T3 | 2025-04 | exc | fab | — | https://theburningmonk.com/2025/04/event-versioning-strategies-for-event-driven-architectures/ |
| research | B3 | T3 | — † | — | fab | — | https://codeopinion.com/event-versioning-guidelines/ |
| research | B3 | T3 | — † | — | cur fab kim | — | https://www.conduktor.io/glossary/schema-evolution-best-practices |
| research | B3 | T3 | — † | — | kim | — | https://www.conduktor.io/glossary/schema-registry-and-schema-management |
| research | B3 | T3 | — † | — | kim | — | https://www.conduktor.io/blog/schema-evolution-avro-compatibility-guide |
| research | B3 | T3 | — † | — | kim | — | https://www.datalane-data.blog/blog/kafka-schema-registry-evolution/ |
| research | B3 | T3 | — † | — | fab | — | https://hookdeck.com/outpost/guides/webhook-versioning-strategies |
| research | B3 | T3 | — † | — | fab | — | https://www.javacodegeeks.com/2025/06/schema-evolution-in-apache-avro-protobuf-and-json-schema.html |
| research | B3 | T3 | — † | — | cur | — | https://letsbuildsolutions.com/blog/system-design/event-schema-versioning-in-practice-evolution-strategies-registry-patterns-and-breaking-change-management-for-production-event-systems/ |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/@zdb.dashti/practical-guide-to-schema-compatibility-in-kafka-f157eee663ef |
| research | B3 | T3 | — † | — | fab kim | — | https://www.nilus.be/blog/event-versioning-strategy-in-kafka-architectures/ |
| research | B3 | T3 | — † | — | fab | — | https://pnguyen.au/posts/es-event-versioning/ |
| research | B3 | T3 | — † | — | fab | — | https://snowplow.io/snowplow-frequently-asked-questions/how-to-handle-schema-evolution-for-kafka-event-data |
| research | B3 | T3 | — † | — | cur | — | https://stackpractices.com/docs/message-schema-evolution-policy/ |
| WILD | B3 | U | — † | — | fab | — | https://blog.stackademic.com/schema-versioning-in-kafka-events-designing-backward-forward-compatible-payloads-in-spring-b3533ee8dac8?gi=e6871b36cbf8 |

### 1.4.1

**Q:** Webhook verification (HMAC signatures, timestamps), replay protection.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/OWASP/CheatSheetSeries/blob/master/cheatsheets_draft/Webhook_Security_Guidelines_Cheat_Sheet.md |
| core | B3 | T1 | — † | — | kim | — | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md |
| core | B3 | T1 | — † | — | kim | — | https://github.com/standard-webhooks/standard-webhooks/ |
| core | B3 | T1 | — † | — | kim | — | https://www.standardwebhooks.com/ |
| core | B3 | T1 | — † | — | kim | — | https://www.standardwebhooks.com/verify |
| primary | B3 | T2 | — † | — | kim | — | https://api.tenovos.com/developer-portal/webhooks/validation |
| primary | B3 | T2 | — † | — | gpt | — | https://developer.zendesk.com/documentation/webhooks/verifying/ |
| primary | B3 | T2 | — † | — | fab | — | https://documentation.hook0.com/tutorials/webhook-authentication |
| primary | B3 | T2 | — † | — | fab | — | https://support.easypost.com/hc/en-us/articles/39826034964237-Webhook-HMAC-Validation |
| primary | B3 | T2 | — † | — | cur | — | https://www.svix.com/resources/webhook-university/security/webhook-security-101/ |
| research | B1 | T3 | 2026-09 | url | gpt | — | https://www.builderproof.org/benchmarks/can-anyone-post-to-your-webhook-endpoint-verification-axis-september-2026 |
| research | B1 | T3 | 2026-09-03 | exc | gpt | — | https://actiondock.app/blog/webhook-signature-verification-ai-agent-callbacks |
| research | B1 | T3 | 2026-08-21 | exc | gpt | — | https://sourcefeed.dev/a/verify-webhook-payloads-hmac-timestamps-and-replay-protection |
| research | B1 | T3 | 2026-07-17 | exc | gpt | — | https://www-test.unifyport.ai/blog/webhook-hmac-replay-protection-retries/ |
| research | B2 | T3 | 2026 | url | cur | — | https://hookray.com/blog/webhook-signature-verification-2026 |
| research | B2 | T3 | 2026-05 | exc | gpt | — | https://techconcepts.org/blog/webhook-security |
| research | B2 | T3 | 2026-05-24 | exc | fab kim gpt | — | https://www.hooklistener.com/learn/webhook-signing-hmac-verification-best-practices |
| research | B2 | T3 | 2026-04-02 | exc | gpt | — | https://botoi.com/blog/webhook-security-hmac-idempotency/ |
| research | B2 | T3 | 2026-03-24 | exc | gpt | — | https://www.finalapproval.ai/blog/hmac-timestamp-replay-window/ |
| research | B2 | T3 | 2026-03-23 | exc | gpt | — | https://www.webhookvault.com/blog/webhook-security-verification-replay-attacks |
| research | B2 | T3 | 2026-03-21 | exc | fab gpt | — | https://www.freelyit.nl/en/blog/api-security-best-practices-2026-03-21 |
| research | B3 | T3 | — † | — | fab | — | https://blog.requestbin.net/webhook-security-best-practices-authentication-data-protection-with-requestbin/ |
| research | B3 | T3 | — † | — | fab | — | https://didit.me/blog/webhook-security-hmac-signature-validation/ |
| research | B3 | T3 | — † | — | fab | — | https://gethook.to/blog/webhook-replay-attack-prevention |
| research | B3 | T3 | — † | — | fab | — | https://www.hooklistener.com/learn/webhook-security-fundamentals |
| research | B3 | T3 | — † | — | cur | — | https://hookwatch.dev/guides/verify-webhook-signatures |
| research | B3 | T3 | — † | — | fab | — | https://hooque.io/guides/webhook-security/ |
| research | B3 | T3 | — † | — | fab | — | https://www.pontil.com/blog/webhook-signature-verification-a-practical-hmac-sha256-guide |
| research | B3 | T3 | — † | — | fab | — | https://prismatic.io/blog/how-secure-webhook-endpoints-hmac/ |
| research | B3 | T3 | — † | — | kim | — | https://www.svix.com/resources/glossary/webhook-signature/ |
| research | B3 | T3 | — † | — | kim | — | https://www.svix.com/resources/glossary/webhook-payload/ |
| research | B3 | T3 | — † | — | kim | — | https://thunderhooks.com/blog/standard-webhooks-specification-explained |
| research | B3 | T3 | — † | — | cur | — | https://verid.dev/blog/hmac-webhook-verification-how-to-validate-signed-webhook-payloads |
| WILD | B2 | U | 2026 | url | fab | — | https://www.opsecforge.com/blog/webhook-signature-validation-hmac-sha256-best-practices-2026 |

### 1.4.2

**Q:** Are external events normalized to the 1.3 envelope at the edge?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/summerwind/cloudevents-webhook-gateway/blob/master/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/summerwind/cloudevents-webhook-gateway |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/nuetzliches/hookaido |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/hookpipe/hookpipe |
| research | B1 | T3 | 2026-08-10 | url | cur | — | https://fransiscuss.com/2026/08/10/facade-api-microservice-azure/ |
| research | B2 | T3 | 2026 | url | cur kim | — | https://truto.one/blog/what-is-webhook-normalization-2026-integration-guide/ |
| research | B2 | T3 | 2026-02-09 | url | cur kim | — | https://oneuptime.com/blog/post/2026-02-09-serverless-event-gateway-kong-knative/view |
| research | B3 | T3 | 2025-10-13 | exc | cur fab | — | https://medium.com/@kaushalsinh73/6-cloudevents-patterns-for-event-driven-platforms-f1b7ef1fefdb |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2508.13434v1 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2305.04532 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/1008.3301 |
| research | B3 | T3 | — † | — | fab | — | https://developer.confluent.io/courses/event-design/normalization-vs-denormalization/ |
| research | B3 | T3 | — † | — | cur | — | https://gethook.to/blog/webhook-payload-transformation-gateway |
| research | B3 | T3 | — † | — | kim | — | https://gethook.to/blog/normalizing-webhook-payloads-unified-event-model |
| research | B3 | T3 | — † | — | kim | — | https://gethook.to/blog/cloudevents-for-webhooks-standard-envelope |
| research | B3 | T3 | — † | — | cur kim | cursor:1.0.1 | https://github.com/NousResearch/hermes-agent/pull/90995 |
| research | B3 | T3 | — † | — | fab | — | https://www.ibm.com/community/z-and-cloud/application-modernization-patterns/respond-to-external-events-pattern/ |
| research | B3 | T3 | — † | — | fab | — | https://pmc.ncbi.nlm.nih.gov/articles/PMC12900004/ |
| WILD | B3 | U | — † | — | fab | — | https://event.foundryco.com/edge-channel-conference/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.googleapis.com/dirsearch-public/print/downloadPdf/8798578 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8630613 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/9208476 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/8694462 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/8595322 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/12530539 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/7779042 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/11507583 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/10685024 |
| WILD | B3 | U | — † | — | kim | — | https://infinisynapse.com/en/blog/webhook-relay-api-data-model |

### 1.4.3

**Q:** Rate limiting, dedup, dead-letter handling — owned where?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/azure/service-bus-messaging/service-bus-dead-letter-queues |
| research | B2 | T3 | 2026 | url | fab | — | https://sdcourse.substack.com/p/day-36-dead-letter-queues-for-failed |
| research | B3 | T3 | — † | — | fab | — | https://airbyte.com/data-engineering-resources/data-deduplication |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2603.13972 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2602.11741 |
| research | B3 | T3 | — † | — | fab | — | https://beefed.ai/en/dead-letter-queue-monitoring-replay |
| research | B3 | T3 | — † | — | fab | — | https://codelit.io/blog/dead-letter-queue-patterns |
| research | B3 | T3 | — † | — | fab | — | https://www.conduktor.io/glossary/dead-letter-queues-for-error-handling |
| research | B3 | T3 | — † | — | cur kim | — | https://dev.to/antfarm-tech/webhooks-at-scale-designing-an-idempotent-replay-safe-and-observable-webhook-system-7lk |
| research | B3 | T3 | — † | — | cur | — | https://www.distributedrequest.com/idempotency-fundamentals-api-guarantees/webhook-delivery-guarantees/ |
| research | B3 | T3 | — † | — | fab | — | https://dl.acm.org/doi/10.1145/3735508 |
| research | B3 | T3 | — † | — | kim | 2.1.5 | https://gethook.to/blog/webhook-deduplication-handling-duplicate-events |
| research | B3 | T3 | — † | — | cur | 5.3.2 | https://github.com/kingsleyonoh/Webhook-Ingestion-Replay-Engine |
| research | B3 | T3 | — † | — | fab | — | https://www.gravitee.io/blog/rate-limiting-apis-scale-patterns-strategies |
| research | B3 | T3 | — † | — | kim | — | https://hookdeck.com/webhooks/guides/dead-letter-queues-webhook-reliability |
| research | B3 | T3 | — † | — | kim | 2.1.5 | https://hookdeck.com/webhooks/guides/how-managed-webhook-services-implement-exactly-once-delivery |
| research | B3 | T3 | — † | — | kim | — | https://hookwatch.dev/guides/webhook-idempotency |
| research | B3 | T3 | — † | — | kim | — | https://resilientbackend.hashnode.dev/building-a-resilient-webhook-ingestion-system-handling-retries-rates-and-idempotency |
| research | B3 | T3 | — † | — | cur | — | https://softwarecrafting.in/blog/bulletproof-webhook-ingestion-architecting-high-throughput |
| research | B3 | T3 | — † | — | kim | — | https://streamkap.com/resources-and-guides/webhook-to-kafka-reliable-ingestion |
| research | B3 | T3 | — † | — | fab | — | https://web-alert.io/blog/dead-letter-queues-explained-handling-failed-messages |
| research | B3 | T3 | — † | — | cur | — | https://webhook-architecture.com/webhook-architecture-fundamentals-design-patterns/idempotency-in-webhooks/storing-idempotency-keys-in-postgres/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Dead_letter_queue |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Rate_limiting |
| WILD | B3 | U | — † | — | kim | — | https://www.kunalganglani.com/blog/design-webhook-delivery-system |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@francotesei/dead-letter-pattern-dont-let-bad-records-kill-your-pipeline-0db338b09f02 |
| WILD | B3 | U | — † | — | kim | — | https://messages.solutions/webhook-queue-integration-patterns |
| WILD | B3 | U | — † | — | fab | — | https://phabricator.wikimedia.org/T173447 |
| WILD | B3 | U | — † | — | fab | — | https://purecommunity.purestorage.com/blog/user-blogs/understanding-deduplication-ratios/3488 |
| WILD | B3 | U | — † | — | fab kim | — | https://vercel.com/i/dead-letter-queue-guide |

### 1.4.4

**Q:** Ingress tool (gateway, function, queue) selection rule.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-06-05 | exc | cur | — | https://kubernetes.io/blog/2025/06/05/introducing-gateway-api-inference-extension/ |
| primary | B3 | T2 | — † | — | cur | cursor:4.2.5 | https://gateway-api-inference-extension.sigs.k8s.io/guides/implementers/ |
| primary | B3 | T2 | — † | — | cur | — | https://gateway-api-inference-extension.sigs.k8s.io/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/kubernetes-sigs/gateway-api-inference-extension/blob/main/site-src/guides/flow-control.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/kubernetes-sigs/gateway-api-inference-extension/tree/main/docs/proposals/0683-epp-architecture-proposal |
| primary | B3 | T2 | — † | — | gpt | 2.1.1 2.1.3 | https://mvp-scale.com/ |
| research | B2 | T3 | 2026 | url | fab | 10.3.5 | https://dev.to/mechcloud_academy/kubernetes-gateway-api-in-2026-the-definitive-guide-to-envoy-gateway-istio-cilium-and-kong-2bkl |
| research | B2 | T3 | 2026 | url | fab | — | https://dev.to/matheus_releaserun/kubernetes-gateway-api-vs-ingress-vs-loadbalancer-what-to-use-in-2026-3l65 |
| research | B3 | T3 | 2025 | url | fab | — | https://www.pomerium.com/blog/best-ingress-controllers-for-kubernetes |
| research | B3 | T3 | — † | — | fab | — | https://alexandre-vazquez.com/nginx-ingress-controller-alternatives/ |
| research | B3 | T3 | — † | — | fab | — | https://github.com/argoproj/argo-helm/issues/3245 |
| research | B3 | T3 | — † | — | fab | — | https://hookdeck.com/webhooks/platforms/hookdeck-event-gateway-vs-temporal-webhook-gateway-and-durable-workflow-orchestrator-comparison |
| research | B3 | T3 | — † | — | fab | — | https://hookdeck.com/webhooks/platforms/best-webhook-gateway-solutions |
| research | B3 | T3 | — † | — | fab | — | https://hookdeck.com/webhooks/platforms/inngest-alternatives |
| research | B3 | T3 | — † | — | fab | — | https://hookdeck.com/webhooks/platforms/best-webhook-management-platforms |
| research | B3 | T3 | — † | — | kim | — | https://hookdeck.com/webhooks/guides/managed-webhook-gateway-vs-diy-queue-backed-infrastructure |
| research | B3 | T3 | — † | — | kim | — | https://hookdeck.com/webhooks/platforms/most-webhook-agents-dont-need-a-workflow-engine |
| research | B3 | T3 | — † | — | kim | — | https://nango.dev/blog/best-webhook-infrastructure-and-management-tools-for-saas-integrations/ |
| WILD | B3 | U | — † | — | kim | — | https://www.buildmvpfast.com/blog/inngest-vs-trigger-dev-vs-bullmq-background-jobs-nextjs-2026 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/12088503 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/12519732 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/7729351 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/7864791 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/7415477 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/12231342 |
| WILD | B3 | U | — † | — | kim | — | https://starterpick.com/guides/webhook-infrastructure-saas-inngest-trigger-dev-bullmq-2026 |

### 1.5.1

**Q:** A2A version; Agent Card publication and discovery; task lifecycle states used.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-08-27 | exc | gpt | — | https://a2a-protocol.org/latest/blog/category/announcements/ |
| core | B2 | T1 | 2026-05-26 | exc | gpt | 1.5.5 | https://github.com/a2aproject/A2A/blob/main/CHANGELOG.md |
| core | B2 | T1 | 2026-03 | age | kim gpt | 1.5.5 | https://github.com/a2aproject/A2A/blob/main/specification/a2a.proto |
| core | B2 | T1 | 2026-03-12 | url | gpt | 9.1 9.2 | https://a2a-protocol.org/dev/blog/2026/03/12/a2a-protocol-ships-v10-production-ready-standard-for-agent-to-agent-communication/ |
| core | B3 | T1 | — † | — | cur kim | 9.2 cursor:9.3.1 cursor:9.3.2 | https://a2a-protocol.org/latest/whats-new-v1/ |
| core | B3 | T1 | — † | — | cur kim | cursor:9.3.4 cursor:9.3.5 | https://a2a-protocol.org/v1.0.0/specification/ |
| core | B3 | T1 | — † | — | fab kim | 1.5.5 2.1.2 5.3.1 | https://a2a-protocol.org/latest/specification/ |
| core | B3 | T1 | — † | — | fab | — | https://a2a-protocol.org/latest/topics/agent-discovery/ |
| core | B3 | T1 | — † | — | kim | — | https://a2a-protocol.org/v1.0.0/whats-new-v1/ |
| core | B3 | T1 | — † | — | kim | — | https://a2a-protocol.org/dev/topics/life-of-a-task/ |
| core | B3 | T1 | — † | — | fab kim gpt | 1.5.2 1.5.4 1.5.5 2.1.2 5.3.1 | https://github.com/a2aproject/A2A/blob/main/docs/specification.md |
| core | B3 | T1 | — † | — | fab gpt | 1.5.4 | https://github.com/a2aproject/A2A/blob/main/docs/topics/agent-discovery.md |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/a2aproject/A2A/blob/main/docs/whats-new-v1.md |
| primary | B1 | T2 | 2026-07-28 | exc | gpt | — | https://github.com/a2aproject/a2a-js/blob/main/CHANGELOG.md |
| primary | B3 | T2 | — † | — | cur fab | 5.3.1 cursor:1.5.4 | https://a2a-protocol.org/latest/topics/life-of-a-task/ |
| primary | B3 | T2 | — † | — | cur | 5.3.1 cursor:1.5.4 | https://a2a-protocol.org/dev/sdk/python/api/a2a.server.agent_execution.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/a2a-protocol-sdk/latest/a2a_protocol_sdk/types/task/enum.TaskState.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/google/A2A/blob/7b900e77/docs/topics/agent-discovery.md |
| primary | B3 | T2 | — † | — | cur | cursor:1.5.4 | https://github.com/google/A2A/blob/main/docs/specification.md |
| research | B2 | T3 | 2026-06 | exc | fab | — | https://arxiv.org/pdf/2606.07866 |
| research | B2 | T3 | 2026-03 | url | fab | 10.1.4 | https://arxiv.org/pdf/2603.00318 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2601.14567 |
| research | B3 | T3 | — † | — | fab | 1.5.5 | https://arxiv.org/pdf/2508.15819 |
| research | B3 | T3 | — † | — | cur | — | https://atlan.com/know/mcp/a2a-protocol-implementation-guide/ |
| research | B3 | T3 | — † | — | cur | — | https://blckalpaca.at/en/knowledge-base/ai-agents/a2a-protocol-basics/agent-cards-und-discovery |
| research | B3 | T3 | — † | — | cur | — | https://stacka2a.dev/blog/a2a-agent-card-explained |
| WILD | B2 | U | 2026-05-28 | exc | gpt | — | https://agentupdate.ai/releases/a2a |
| WILD | B3 | U | — † | — | kim | — | https://deepwiki.com/a2aproject/A2A/2.4-agent-discovery-via-agentcard |
| WILD | B3 | U | — † | — | fab | 2.4.5 8.5.2 9.4 9.5 | https://en.wikipedia.org/wiki/Agent2Agent |
| WILD | B3 | U | — † | — | kim | — | https://www.hivebook.wiki/wiki/a2a-agent-discovery |
| WILD | B3 | U | — † | — | cur | — | https://medium.com/amex-gbt-technology/introduction-to-agent-to-agent-a2a-protocol-eb4941bff2d5 |

### 1.5.2

**Q:** Trust model between agents (internal vs external); how caller identity is propagated.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-09-04 | exc | gpt | — | https://mailarchive.ietf.org/arch/msg/i-d-announce/2x6neqO6AvVRzl5whBQ9Yds7YAs/ |
| core | B1 | T1 | 2026-08 | url | cur | 1.5.3 | https://arxiv.org/html/2608.16402v1 |
| core | B1 | T1 | 2026-07-06 | exc | gpt | — | https://datatracker.ietf.org/doc/html/draft-fane-opena2a-aip-00 |
| core | B2 | T1 | 2026-04-15 | exc | gpt | — | https://github.com/a2aproject/A2A/discussions/1752 |
| core | B3 | T1 | — † | — | fab gpt | 1.5.4 5.3.1 | https://a2a-protocol.org/v0.3.0/specification/ |
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/html/draft-liu-oauth-a2a-profile-00 |
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/draft-ietf-oauth-transaction-tokens/ |
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/html/draft-araut-oauth-transaction-tokens-for-agents-02 |
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/draft-oauth-transaction-tokens-for-agents/05/ |
| core | B3 | T1 | — † | — | cur | — | https://www.ietf.org/archive/id/draft-lundholm-kaif-00.html |
| core | B3 | T1 | — † | — | cur | — | https://www.ietf.org/archive/id/draft-sharma-oauth-identity-propagation-context-01.html |
| core | B3 | T1 | — † | — | kim | — | https://www.ietf.org/archive/id/draft-singla-agent-identity-protocol-02.html |
| core | B3 | T1 | — † | — | cur fab kim | 10.1.1 10.1.10 | https://spiffe.io/docs/latest/deploying/svids/ |
| primary | B3 | T2 | — † | — | fab kim | — | https://architect.salesforce.com/docs/architect/fundamentals/guide/end-user-identity-propagation |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/XPRNetwork/xpr-agents/blob/main/docs/A2A.md |
| research | B1 | T3 | 2026-09-04 | exc | gpt | — | https://ftp.otenet.gr/doc/internet-drafts/draft-tonyai-a2a-trust-03.html |
| research | B2 | T3 | 2026-05 | exc | fab | — | https://arxiv.org/pdf/2605.05440 |
| research | B2 | T3 | 2026-05-21 | exc | fab | — | https://next.redhat.com/2026/05/21/zero-trust-for-ai-agents-why-delegation-beats-impersonation/ |
| research | B2 | T3 | 2026-03 | exc | fab | — | https://arxiv.org/pdf/2603.18043 |
| research | B2 | T3 | 2026-03 | url | kim | — | https://arxiv.org/html/2603.24775v1 |
| research | B3 | T3 | 2025-03 | url | cur | — | https://www.spletzer.com/2025/03/zero-to-trusted-spiffe-and-spire-demystified/ |
| research | B3 | T3 | — † | — | gpt | — | https://www.agentidentitytrustprotocol.io/docs/architecture |
| research | B3 | T3 | — † | — | gpt | — | https://www.agentidentitytrustprotocol.io/spec/manifest |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2504.16736 |
| research | B3 | T3 | — † | — | cur | — | https://blog.christianposta.com/explaining-on-behalf-of-for-ai-agents/ |
| research | B3 | T3 | — † | — | fab | — | https://github.com/MicrosoftDocs/entra-docs/blob/main/docs/agent-id/agent-tokens.md |
| research | B3 | T3 | — † | — | kim | — | https://github.com/a2aproject/A2A/issues/1575 |
| research | B3 | T3 | — † | — | kim | — | https://mnemoverse.com/docs/library/how-ai-agents-trust-each-other |
| research | B3 | T3 | — † | — | kim | — | https://opena2a.org/identity |
| research | B3 | T3 | — † | — | fab | — | https://www.penligent.ai/hackinglabs/ai-agent-identity-security/ |
| research | B3 | T3 | — † | — | cur fab kim | 10.1.3 | https://www.scrambleid.com/learn/multi-hop-agent-delegation-chains |
| research | B3 | T3 | — † | — | fab | — | https://www.truefoundry.com/blog/authorization-propagation-multi-agent-invariants |
| WILD | B1 | U | 2026-09-10 | age | gpt | — | https://www.financialexpress.com/business/banking-finance-setty-bats-for-know-your-agent-framework-as-ai-enters-banking-4336334/ |
| WILD | B1 | U | 2026-09-04 | exc | gpt | — | https://mirrors.aliyun.com/ietf/draft-tonyai-a2a-trust-03.html |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/articles/inter-agent-trust-is-the-missing-control-in-multi-agent-governance/ |

### 1.5.3

**Q:** Max delegation depth, loop prevention, budget inheritance.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | — | https://assets.publishing.service.gov.uk/media/69e0b1be20b52e41448688cc/Delegated_Authority_Guidance_-_expenditure_categories_subject_to_specific_controls_-_April_2026.pdf |
| primary | B3 | T2 | — † | — | cur kim | — | https://github.com/veegee82/agent-workflow-protocol/blob/main/docs/compliance.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/veegee82/agent-workflow-protocol/blob/4d1fba4b/docs/orchestration.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/veegee82/agent-workflow-protocol/blob/main/docs/manager-intelligence.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/terrene-foundation/kailash-py/blob/main/workspaces/_archive/kaizen-l3/03-user-flows/01-delegation-flow.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/davidahmann/fde-guide/blob/7d1d11f7/blueprints/multi-agent-coordinator.md |
| research | B1 | T3 | 2026-08 | url | kim | — | https://arxiv.org/pdf/2608.15888 |
| research | B3 | T3 | — † | — | kim | — | https://agenticcontrolplane.com/spec/delegation-chain |
| research | B3 | T3 | — † | — | kim | — | https://agenticcontrolplane.com/blog/introducing-adcs-delegation-chain-spec |
| research | B3 | T3 | — † | — | kim | — | https://agenticcontrolplane.com/agent-to-agent |
| research | B3 | T3 | — † | — | cur | — | https://github.com/anis-marrouchi/agentx/blob/master/docs/playbooks/capability-audit.md |
| research | B3 | T3 | — † | — | cur | — | https://github.com/happyvertical/smrt/blob/main/packages/agents/src/delegation.ts |
| research | B3 | T3 | — † | — | cur | — | https://github.com/xmiksay/entanglement/blob/master/docs/adr/0023-subagent-spawn-limits.md |
| research | B3 | T3 | — † | — | kim | — | https://github.com/agentic-control-plane/delegation-chain-spec/blob/main/SPEC.md |
| WILD | B3 | U | 2025 | url | fab | — | https://www.delegatesolutions.com/state-of-delegation |
| WILD | B3 | U | — † | — | fab | — | https://www.darwingray.com/autumn-budget-business-property-relief-and-the-changes-that-may-affect-you-and-your-business-in-2026/ |
| WILD | B3 | U | — † | — | fab | 2.3.4 3.1.1 3.1.3 3.1.6 3.5.3 4.3.1 8.1.4 | https://github.com/ai-boost/awesome-harness-engineering |
| WILD | B3 | U | — † | — | fab | — | https://pi.dev/packages/@tintinweb/pi-subagents |
| WILD | B3 | U | — † | — | fab | — | https://procurementbd.com/act-rule/dofp-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.whitehouse.gov/wp-content/uploads/2025/05/appendix_fy2026.pdf |

### 1.5.4

**Q:** Agent Card trust: is the card (1.5.1) signed and the signer verified before declared capabilities are relied on; fetched from the registry (8.5) or a well-known URI; how are revoked or stale cards detected?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-06 | exc | kim | — | https://www.ietf.org/archive/id/draft-ayoub-agis-agent-identity-system-00.txt |
| core | B3 | T1 | — † | — | gpt | 2.1.2 | https://a2a-protocol.org/dev/specification/ |
| core | B3 | T1 | — † | — | kim gpt | 5.3.1 | https://agentic-web.one/a2a/reference/specification/ |
| core | B3 | T1 | — † | — | kim | — | https://github.com/a2aproject/A2A/discussions/1803 |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/a2aproject/A2A/diffs/0?base_sha=290c87f0c221b2423e4611a476e67187eda9773e&head_user=msardara&name=main&pull_number=1303&qualified_name=refs%2Fheads%2Fmain&sha1=290c87f0c221b2423e4611a476e67187eda9773e&sha2=d63daacc2c3c19258e6c3b1a47ddd786c7b0b5f6&short_path=eebad86&unchanged=expanded&w=false |
| primary | B3 | T2 | — † | — | kim | — | https://docs.a2d-ai.com/features/agent-cards/signed-agent-cards/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/a2a-protocol-sdk/latest/a2a_protocol_sdk/types/signing/fn.verify_agent_card.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/a2a-protocol-types/latest/a2a_protocol_types/signing/fn.verify_agent_card.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/a2a-protocol-types/latest/src/a2a_protocol_types/signing.rs.html |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/a2aproject/a2a-tck/blob/main/.agents/skills/a2a-client/references/specification.md |
| research | B1 | T3 | 2026-09-05 | exc | gpt | — | https://a2atraffic.com/ |
| research | B3 | T3 | — † | — | kim | — | https://www.agentcard.net/agent-card-schema |
| research | B3 | T3 | — † | — | kim | — | https://api7.ai/blog/a2a-protocol-gateway-layer |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2606.04193 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2507.14263 |
| research | B3 | T3 | — † | — | kim | — | https://blog.tobira.ai/how-a2a-agent-cards-work/ |
| research | B3 | T3 | — † | — | fab | — | https://securew2.com/blog/everything-you-need-to-know-about-certificate-pinning |
| research | B3 | T3 | — † | — | fab | — | https://securew2.com/blog/certificate-pinning-vs-device-attestation |
| WILD | B1 | U | 2026-08-29 | exc | gpt | — | https://www.a2a-registry.org/agent/io.sslip.a2a |
| WILD | B2 | U | 2026-04 | exc | fab | — | https://eco.com/support/en/articles/15192005-agent-identity-verification-how-ai-agents-authenticate-purchases-in-2026 |
| WILD | B3 | U | — † | — | fab | — | https://4sysops.com/archives/microsoft-entra-certificate-change-what-admins-need-to-do-now/ |
| WILD | B3 | U | — † | — | kim gpt | — | https://www.a2a-registry.org/resources/spec |
| WILD | B3 | U | — † | — | fab | — | https://github.com/a2aproject/A2A/issues/1672 |
| WILD | B3 | U | — † | — | fab | — | https://www.godaddy.com/ans |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/11765155 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/10812275 |

### 1.5.5

**Q:** A2A push notifications for long-running tasks (per-task webhook registration and auth): supported, and do they reuse the notification port (5.3.2) or a separate A2A channel?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab gpt | — | https://a2a-protocol.org/latest/topics/streaming-and-async/ |
| core | B3 | T1 | — † | — | fab | — | https://a2a-protocol.org/v0.2.4/specification/ |
| core | B3 | T1 | — † | — | kim | — | https://a2a-protocol.org/dev/topics/streaming-and-async/ |
| core | B3 | T1 | — † | — | kim | — | https://a2a-protocol.org/v0.2.6/topics/streaming-and-async/ |
| core | B3 | T1 | — † | — | gpt | — | https://a2a-protocol.org/v0.3.0/topics/streaming-and-async/ |
| core | B3 | T1 | — † | — | gpt | — | https://a2aproject.github.io/A2A/latest/specification/ |
| core | B3 | T1 | — † | — | fab | — | https://agent2agent.info/docs/topics/streaming-and-async/ |
| core | B3 | T1 | — † | — | fab kim gpt | — | https://github.com/a2aproject/A2A/blob/main/docs/topics/streaming-and-async.md |
| core | B3 | T1 | — † | — | kim | — | https://github.com/a2aproject/A2A/blob/2183794b/docs/topics/streaming-and-async.md |
| core | B3 | T1 | — † | — | gpt | 2.1.2 | https://github.com/a2aproject/A2A/blob/main/docs/specification.md?plain=1 |
| primary | B2 | T2 | 2026-03-19 | exc | gpt | — | https://github.com/a2aproject/a2a-python/issues/875 |
| primary | B3 | T2 | — † | — | kim | — | https://archestra.ai/docs/platform-agent-triggers-webhook-a2a |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/a2aproject/a2a-python/pull/394 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/a2aproject/a2a-python/issues/239 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2505.21550 |
| research | B3 | T3 | — † | — | fab | 2.1.2 | https://www.glukhov.org/ai-systems/architecture/a2a-streaming-async-task-lifecycle |
| research | B3 | T3 | — † | — | kim | — | https://www.glukhov.org/ai-systems/architecture/a2a-streaming-async-task-lifecycle/ |
| research | B3 | T3 | — † | — | fab | — | https://www.standupalice.com/post/year-in-review-what-we-learned-about-async-communication-in-2025 |
| research | B3 | T3 | — † | — | fab | — | https://workos.com/blog/mcp-async-tasks-ai-agent-workflows |
| WILD | B2 | U | 2026 | url | fab | 2.1.2 2.4.5 | https://eco.com/support/en/articles/14845481-a2a-agent-to-agent-protocol-explained |
| WILD | B3 | U | — † | — | kim | — | https://a2aprotocol.ai/docs/guide/a2a-protocol-specification-python |
| WILD | B3 | U | — † | — | fab | — | https://www.agentcenter.cloud/blogs/complete-guide-ai-agent-management-2026 |
| WILD | B3 | U | — † | — | fab | — | https://blckalpaca.at/en/blog/agentic-ai-design-patterns-for-2026-build-trustworthy-systems |
| WILD | B3 | U | — † | — | fab | — | https://hermes-agent.nousresearch.com/docs/user-guide/messaging/a2a |
| WILD | B3 | U | — † | — | fab | — | https://www.myweirdprompts.com/episode/agent-architecture-sync-async/ |
| WILD | B3 | U | — † | — | fab | 5.3.1 9.4 | https://tyk.io/learning-center/a2a-protocol-architecture-and-technical-specification/ |

## 2. Orchestration & Control Plane

### 2.1.1

**Q:** Do all five entry types (1.1–1.5) converge on one canonical work-request envelope here? Schema and version.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/draft-cowles-aee/01/ |
| primary | B3 | T2 | — † | — | cur kim | cursor:1.0.1 | https://github.com/openwop/openwop/blob/main/spec/v1/ai-envelope.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/Agents/issues/472 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/eccentricnode/agency-icm/blob/main/HANDOFF_SCHEMA.md |
| primary | B3 | T2 | — † | — | gpt | — | https://mvp-scale.com/changelog |
| research | B3 | T3 | — † | — | kim | — | https://www.agent-native.com/hi-IN/docs/template-dispatch-messaging-routing |
| research | B3 | T3 | — † | — | fab | — | https://www.confluent.io/blog/building-real-time-multi-agent-ai/ |
| research | B3 | T3 | — † | — | fab | — | https://hookdeck.com/webhooks/guides/webhooks-ai-agents-integration-patterns |
| research | B3 | T3 | — † | — | kim | — | https://leena.ai/platform/orchestrator |
| WILD | B2 | U | 2026 | url | fab | 2.1.6 | https://www.buildmvpfast.com/blog/webhook-driven-agent-architecture-event-based-triggers-autonomous-ai-workflows-2026 |
| WILD | B2 | U | 2026 | exc | fab kim | 2.3.1 2.4.8 | https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.ivalua.com/blog/procurement-orchestration/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.ivalua.com/blog/ai-in-procurement-orchestration/ |
| WILD | B2 | U | 2026 | exc | fab | 2.1.4 | https://newsletter.pureprocurement.ca/p/procurement-intake-orchestration-complete-guide |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.speclens.ai/blog/orchestration-vs-specification-intelligence |
| WILD | B2 | U | 2026 | url | fab | — | https://www.swfte.com/blog/ai-workflow-orchestration-patterns-2026 |
| WILD | B3 | U | — † | — | fab | — | https://agentdraft.io/blog/agentic-email-inbox-webhooks-architecture |
| WILD | B3 | U | — † | — | fab | — | https://www.apideck.com/blog/what-is-a-webhook |
| WILD | B3 | U | — † | — | fab | — | https://www.developersdigest.tech/blog/deploy-agent-webhook-railway |
| WILD | B3 | U | — † | — | fab | — | https://docs.agentmail.to/events |
| WILD | B3 | U | — † | — | kim | — | https://github.laiyagushi.com/useorgx/agent-work-receipt |
| WILD | B3 | U | — † | — | fab | — | https://www.hyperagent.com/docs/concepts/agents/invocations/webhooks |
| WILD | B3 | U | — † | — | fab | — | https://zip.com/blog/intake-vs-procurement-orchestration |

### 2.1.2

**Q:** Is an inbound A2A task (1.5) treated as just another intake?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://a2a-protocol.org/ |
| core | B3 | T1 | — † | — | gpt | — | https://a2a-protocol.org/v0.2.6/specification/ |
| core | B3 | T1 | — † | — | fab | — | https://datatracker.ietf.org/doc/draft-yang-nmrg-a2a-nm/ |
| primary | B1 | T2 | 2026-08 | age | gpt | — | https://github.com/a2aproject/a2a-cli/blob/main/specification/SPEC.md |
| primary | B3 | T2 | — † | — | kim | — | https://codelabs.developers.google.com/intro-a2a-purchasing-concierge |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.oracle.com/en/cloud/saas/fusion-ai/26c/aiaas/api-overview.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/google/a2a-python/blob/fa14dbf4/src/a2a/server/request_handlers/default_request_handler.py |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/NousResearch/hermes-agent/pull/41711 |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/microsoftteams/platform/teams-sdk/in-depth-guides/ai-integrations/a2a |
| primary | B3 | T2 | — † | — | kim | — | https://www.npmjs.com/package/@aramisfa/openclaw-a2a-inbound |
| research | B2 | T3 | 2026-03-28 | url | gpt | 2.4.5 | https://arxiv.org/abs/2603.27299 |
| research | B2 | T3 | 2026-02 | url | fab | — | https://camunda.com/blog/2026/02/using-a2a-to-achieve-your-business-goals-pt-1/ |
| research | B3 | T3 | — † | — | gpt | — | https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-frameworks/getting-started-with-a2-a.html |
| research | B3 | T3 | — † | — | kim | — | https://docs.xpander.ai/guides/agents/deploy-agent |
| research | B3 | T3 | — † | — | kim | — | https://pub.towardsai.net/a2a-protocol-v1-2026-how-ai-agents-actually-talk-to-each-other-c500079bca73 |
| WILD | B2 | U | 2026 | url | fab | — | https://dailyaiworld.com/workflow/a2a-protocol-guide-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://dev.to/chunxiaoxx/building-multi-agent-ai-systems-in-2026-a2a-observability-and-verifiable-execution-10gn |
| WILD | B2 | U | 2026 | url | fab | — | https://devops.gheware.com/blog/posts/google-a2a-protocol-enterprise-multi-agent-2026.html |
| WILD | B2 | U | 2026 | url | fab | 2.4.5 | https://www.glukhov.org/ai-systems/comparisons/a2a-protocol-2026-adoption/ |
| WILD | B2 | U | 2026 | url | fab | — | https://niteagent.com/blog/a2a-protocol-guide-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://onereach.ai/blog/what-is-a2a-agent-to-agent-protocol/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/mcp/mcp-vs-a2a-protocol/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/google-a2a-protocol/ |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/luigisaetta/a2a-procurement-agents/blob/main/AGENT_CATALOG.md |

### 2.1.3

**Q:** Required fields: tenancy, priority, budget, data classification.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://data.catering/0.19.1/docs/guide/data-source/metadata/json-schema/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.agent-swarm.dev/docs/concepts/task-lifecycle |
| primary | B3 | T2 | — † | — | kim | — | https://docs.beam.ai/08-reference/api/agent-task/create-agent-task |
| primary | B3 | T2 | — † | — | fab | — | https://docs.cloud.google.com/architecture/multi-tenant-agentic-ai-system |
| primary | B3 | T2 | — † | — | kim | — | https://docs.taskpod.ai/api/tasks/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/factset/enterprise-sdk/blob/main/code/dotnet/Vermilion/v1/docs/ReportGenerationRequest.md |
| primary | B3 | T2 | — † | — | cur | — | https://raw.githubusercontent.com/api-evangelist/factset/refs/heads/main/openapi/factset-generate-api-openapi.yml |
| primary | B3 | T2 | — † | — | cur | — | https://raw.githubusercontent.com/api-evangelist/factset/refs/heads/main/openapi/factset-report-api-openapi.yml |
| primary | B3 | T2 | — † | — | cur | — | https://raw.githubusercontent.com/api-evangelist/factset/refs/heads/main/openapi/factset-report-instances-api-openapi.yml |
| research | B3 | T3 | — † | — | kim | 3.4.3 | https://www.agentpatterns.tech/en/architecture/multi-tenant |
| research | B3 | T3 | — † | — | fab kim | — | https://aws.amazon.com/blogs/machine-learning/shared-infrastructure-isolated-tenants-pool-model-multi-tenancy-with-amazon-bedrock-agentcore/ |
| research | B3 | T3 | — † | — | fab | — | https://aws.amazon.com/blogs/machine-learning/building-multi-tenant-agents-with-amazon-bedrock-agentcore/ |
| research | B3 | T3 | — † | — | kim | — | https://colrows.com/blogs/how-to-govern-ai-agents-that-query-enterprise-data/ |
| research | B3 | T3 | — † | — | fab | — | https://engineering.salesforce.com/building-a-multi-tenant-ai-agent-platform-handling-7k-sessions/ |
| research | B3 | T3 | — † | — | kim | — | https://hyperdrift.io/blog/multi-tenant-agent-architecture |
| research | B3 | T3 | — † | — | kim | — | https://labs.strongstart.digital/multi-tenancy-guide-for-ipaas-mcp-architecture-notes |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/ai-agent/how-to-structure-context-for-ai-agents/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.explorium.ai/blog/data-for-gtm/intent-data-for-ai-sales-agents/ |
| WILD | B2 | U | 2026 | exc | fab | 7.2.2 10.1.6 | https://fast.io/resources/ai-agent-multi-tenant-architecture/ |
| WILD | B2 | U | 2026 | url | fab | — | https://truto.one/blog/mapping-ai-agent-patterns-to-integration-platforms-2026-tutorial/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.usefini.com/guides/ai-support-platforms-tenant-isolated-ml-models-banking-compliance |
| WILD | B2 | U | 2026-05-07 | url | fab | 3.4.3 7.2.2 | https://zylos.ai/research/2026-05-07-ai-agent-multi-tenant-architecture/ |
| WILD | B3 | U | — † | — | fab | — | https://callsphere.ai/blog/ai-tenant-support-agent-maintenance-requests-rent-inquiries-lease-questions |
| WILD | B3 | U | — † | — | fab | — | https://callsphere.ai/blog/ai-agent-saas-architecture-multi-tenant-platform-design |
| WILD | B3 | U | — † | — | kim | — | https://feeds.trussed.ai/blog/multi-tenancy-ai-service-cost-allocation |
| WILD | B3 | U | — † | — | fab | — | https://oncallclerk.com/blog/manage-tenant-enquiries-maintenance-calls |
| WILD | B3 | U | — † | — | fab | — | https://taskestate.com/maintenance-request-workflow |

### 2.1.4

**Q:** Enrichment sources and failure behaviour when a source is unavailable.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://automem.ai/docs/architecture/enrichment/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/jeremylongshore/claude-code-plugins-plus-skills/blob/3022dd3eead80be2512aa933344ce986c0fcbdf7/plugins/saas-packs/clay-pack/skills/clay-reliability-patterns/SKILL.md |
| research | B1 | T3 | 2026-08 | url | fab | — | https://arxiv.org/html/2608.05263 |
| research | B2 | T3 | 2026-06 | exc | kim | — | https://medium.com/@almogalmado/inside-our-streaming-enrichment-service-architecture-and-motivation-8aa97fc526f4 |
| research | B2 | T3 | 2026-06 | exc | kim | — | https://medium.com/@almogalmado/the-hard-parts-of-real-time-event-enrichment-cdc-caching-and-hot-path-optimization-5a80db7c40ba |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.14102 |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.27891 |
| research | B2 | T3 | 2026-02-20 | url | fab | — | https://zylos.ai/research/2026-02-20-graceful-degradation-ai-agent-systems/ |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.24380 |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/banso-labs/banso/5.1-enrichment-registry-and-steps |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/forgeflows/why-ai-lead-enrichment-agents-fail-in-production-kk4 |
| research | B3 | T3 | — † | — | cur | — | https://levelop.dev/blog/fault-tolerant-ai-agent-pipeline-error-recovery |
| research | B3 | T3 | — † | — | kim | — | https://www.logparsing.com/soar-playbook-automation/case-enrichment-pipelines/ |
| research | B3 | T3 | — † | — | cur | — | https://nhimg.org/faq/what-breaks-when-soc-automation-rules-are-ordered-poorly-or-enrichment-sources-t/ |
| research | B3 | T3 | — † | — | cur | — | https://pub.towardsai.net/fault-tolerant-agent-pipelines-checkpoint-retry-and-compensate-8870ed221c26 |
| research | B3 | T3 | — † | — | kim | — | https://unstructured.io/insights/managing-dependencies-in-data-workflows-a-practical-guide |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/graceful-degradation-ai-agents-fallback-model-unavailable-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://cogentinfo.com/resources/when-ai-agents-collide-multi-agent-orchestration-failure-playbook-for-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://dev.to/young_gao/graceful-degradation-4b5p |
| WILD | B3 | U | — † | — | fab kim | 3.2.5 | https://backendbytes.com/articles/llm-provider-outage-resilience/ |
| WILD | B3 | U | — † | — | kim | — | https://databar.ai/blog/article/best-lead-enrichment-apis-for-developers-2025 |
| WILD | B3 | U | — † | — | fab | — | https://www.devopsschool.nl/graceful-degradation/ |
| WILD | B3 | U | — † | — | fab | 2.3.1 2.4.8 | https://www.glukhov.org/ai-systems/architecture/multi-agent-orchestration-patterns/ |
| WILD | B3 | U | — † | — | fab | — | https://www.lyzr.ai/blog/agent-orchestration/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@bhargava.akki/the-static-fallback-architecture-a-blueprint-for-graceful-degradation-e114263a7b10 |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/faq/what-breaks-when-error-handling-is-missing-in-multi-agent-orchestration/ |

### 2.1.5

**Q:** Idempotency/dedup here or at the entry point (1.x)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-10 | exc | fab | 10.3.2 | https://www.ietf.org/archive/id/draft-ietf-httpapi-idempotency-key-header-07.html |
| core | B3 | T1 | — † | — | fab | — | https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header |
| core | B3 | T1 | — † | — | fab | 10.3.2 | https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-00 |
| primary | B3 | T2 | — † | — | cur | — | https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentrel06-bp04.html |
| research | B1 | T3 | 2026-07-05 | url | cur fab | 10.3.2 | https://tianpan.co/blog/2026/07/05/the-idempotency-key-your-agent-forgot-to-send |
| research | B1 | T3 | 2026-07-01 | url | cur | 10.3.2 | https://tianpan.co/blog/2026/07/01/exactly-once-was-hard-before-your-agent-could-retry-itself |
| research | B2 | T3 | 2026-04-24 | url | fab | 2.3.4 4.3.2 | https://zylos.ai/research/2026-04-24-durable-execution-agent-runtimes/ |
| research | B2 | T3 | 2026-04-23 | url | cur | — | https://tianpan.co/blog/2026/04/23/agent-idempotency-orchestration-contract |
| research | B2 | T3 | 2026-04-19 | url | fab | 10.3.2 | https://tianpan.co/blog/2026/04/19/idempotency-agentic-tool-calling-saga-deduplication |
| research | B3 | T3 | — † | — | kim | — | https://aloknecessary.in/blogs/idempotency-distributed-systems/ |
| research | B3 | T3 | — † | — | fab | 5.1.4 | https://aws.amazon.com/blogs/compute/building-fault-tolerant-multi-agent-ai-workflows-with-aws-lambda-durable-functions/ |
| research | B3 | T3 | — † | — | fab | — | https://aws.amazon.com/marketplace/build-learn/ai-agent-learning-series/agent-orchestration |
| research | B3 | T3 | — † | — | kim | — | https://www.distributedrequest.com/backend-implementation-storage-patterns/ |
| research | B3 | T3 | — † | — | kim | — | https://www.hooklistener.com/learn/webhook-idempotency-and-deduplication |
| research | B3 | T3 | — † | — | cur | — | https://www.linkedin.com/pulse/designing-idempotent-write-operations-business-agents-michel-tricot-venic |
| research | B3 | T3 | — † | — | cur | — | https://loopandretry.github.io/posts/idempotency-keys-for-agents/ |
| research | B3 | T3 | — † | — | kim | — | https://www.pontil.com/blog/webhook-reliability-patterns-how-to-deliver-events-agents |
| research | B3 | T3 | — † | — | kim | — | https://scalemind.dev/java/microservices/architecture/microservices-idempotency-dedupe-store-part-1/ |
| research | B3 | T3 | — † | — | kim | — | https://webhookrelay.com/blog/webhook-retries-and-idempotency/ |
| WILD | B2 | U | 2026 | url | fab | 10.3.2 | https://www.alekseialeinikov.com/en/blog/topics/architecture/idempotency-in-practice-api-retries-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/idempotent-ai-agent-retry-safe-patterns-production-workflow-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.cloudopsnow.in/idempotency/ |
| WILD | B2 | U | 2026 | url | fab | — | https://knowledgelib.io/software/patterns/idempotency-patterns/2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.activepieces.com/blog/webhook-idempotency-keys-how-to-stop-duplicate-runs |
| WILD | B3 | U | — † | — | fab | — | https://bhavishyapandit9.substack.com/p/idempotency-and-retry-semantics-for |
| WILD | B3 | U | — † | — | fab | — | https://www.glukhov.org/app-architecture/integration-patterns/idempotency-in-distributed-systems/ |
| WILD | B3 | U | — † | — | fab | — | https://vadim.blog/durable-execution-llm-agents/ |
| WILD | B3 | U | — † | — | kim | — | https://zerq.dev/blog/idempotent-payment-api-gateway-workflow-redis |

### 2.1.6

**Q:** Rejection contract per entry type.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2023-07 | exc | fab | — | https://datatracker.ietf.org/doc/html/rfc9457 |
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/draft-ratnawat-httpapi-async-problem-details/ |
| core | B3 | T1 | — † | — | kim | — | https://www.ietf.org/archive/id/draft-ratnawat-httpapi-async-problem-details-00.html |
| core | B3 | T1 | — † | — | fab | — | https://www.rfc-editor.org/info/rfc9457/ |
| core | B3 | T1 | — † | — | kim | — | https://www.rfc-editor.org/rfc/rfc9457.html |
| primary | B1 | T2 | 2026-07 | url | cur | — | https://www.cbp.gov/sites/default/files/2026-07/26_0720_ace_catair_entry_summary_query_future.pdf |
| primary | B2 | T2 | 2026-05 | url | cur | — | https://www.cbp.gov/sites/default/files/2026-05/ace_catair_entry_summary_query_may_2026_v26_508.pdf |
| primary | B3 | T2 | — † | — | cur | — | https://www.cbp.gov/document/technical-documentation/entry-summary-acceptance-and-reject-process |
| primary | B3 | T2 | — † | — | cur | — | https://www.cbp.gov/sites/default/files/documents/3550-067_3.pdf |
| primary | B3 | T2 | — † | — | cur | — | https://www.cbsa-asfc.gc.ca/publications/dm-md/d17/d17-1-4-eng.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/NousResearch/hermes-agent/issues/491 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/dotnet/runtime/issues/131046 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/auto-agent-protocol/auto-agent-protocol/blob/main/versioned_docs/version-v1.1/errors.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/vassiliylakhonin/grantflow/blob/main/docs/agents/error-contract.md |
| research | B3 | T3 | — † | — | kim | — | https://agenthermes.ai/blog/structured-errors-guide |
| research | B3 | T3 | — † | — | kim | — | https://agentpatterns.ai/tool-engineering/rfc9457-machine-readable-errors/ |
| research | B3 | T3 | — † | — | kim | — | https://geodocs.dev/ai-agents/agent-error-handling-documentation-spec |
| WILD | B1 | U | 2026-07 | exc | fab | — | https://www.digitalapplied.com/blog/amp-event-driven-orbs-self-scheduling-agents-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://noopsschool.com/blog/admission-webhook/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://signb.ee/blog/straight-through-contract-execution-api |
| WILD | B3 | U | — † | — | fab | — | https://agntapi.com/my-webhook-strategy-for-agent-apis/ |
| WILD | B3 | U | — † | — | fab | — | https://cal.com/docs/developing/guides/automation/webhooks |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/abdelrani/error-handling-in-spring-web-using-rfc-9457-specification-5dj1 |
| WILD | B3 | U | — † | — | fab | — | https://developers.sparkpost.com/api/webhooks/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/t1/problem-details |
| WILD | B3 | U | — † | — | fab | — | https://github.com/paveg/hono-problem-details |
| WILD | B3 | U | — † | — | fab | — | https://www.learnhubly.com/blog/rfc-9457-problem-details-api-error-responses |
| WILD | B3 | U | — † | — | fab | — | https://rfcinfo.com/rfc-9457/ |

### 2.2.1

**Q:** Evaluation points: intake, plan approval, each tool call, each model call, output admission.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | exc | cur | — | https://github.com/davidahmann/fde-guide/blob/7d1d11f7/library/04-production-evaluation-and-governance.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-governance-toolkit/tree/main/policy-engine |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-governance-toolkit/blob/main/policy-engine/spec/SPECIFICATION.md |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/agent-framework/agents/agent-hooks |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/agent-governance-toolkit/packages/agent-control-specification/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.truefoundry.com/docs/agent-platform/agent-governance/agent-guardrails |
| research | B1 | T3 | 2026-09 | age | fab | 4.3.7 10.2.3 | https://www.sweet.security/agent-security/ai-agent-policy-enforcement |
| research | B2 | T3 | 2026 | url | cur kim | — | https://futureagi.com/blog/evaluating-tool-calling-agents-2026/ |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/html/2603.20953v1 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.20953 |
| research | B3 | T3 | — † | — | fab kim | 7.1.3 | https://www.confident-ai.com/blog/llm-agent-evaluation-complete-guide |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/black_shadow_team/chapter-43-ai-agents-planning-tool-calling-task-state-permission-boundaries-human-approval--pfc |
| research | B3 | T3 | — † | — | kim | — | https://langfuse.com/resources/engineering/ai-agent-evaluation |
| research | B3 | T3 | — † | — | fab | — | https://predictionguard.com/blog/runtime-ai-policy-enforcement |
| research | B3 | T3 | — † | — | cur | — | https://sailokeshdevathi.hashnode.dev/how-to-evaluate-llm-agents-in-production |
| research | B3 | T3 | — † | — | cur | — | https://sreekarreddy.com/ai-posts/evaluating-agent-trajectories |
| research | B3 | T3 | — † | — | fab | — | https://www.sweet.security/agent-security/ai-runtime-policy-enforcement |
| research | B3 | T3 | — † | — | fab | — | https://www.truefoundry.com/blog/what-is-ai-policy-enforcement |
| WILD | B2 | U | 2026 | exc | fab | — | https://allainews.net/ai-agent-testing-and-evaluation/ |
| WILD | B2 | U | 2026 | exc | fab | 7.1.3 | https://www.ampcome.com/post/ai-agent-evaluation-framework |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/state-of-ai-agents-2026-200-data-points |
| WILD | B2 | U | 2026 | url | fab | 2.3.4 | https://kingy.ai/news/the-state-of-ai-agents-in-2026-a-practitioners-guide/ |
| WILD | B2 | U | 2026 | url | fab | — | https://kontext.security/content/ai-agents-compliance-security-teams-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.kunalganglani.com/blog/ai-agent-evaluation-framework-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://ones.com/blog/tool-guide/platforms-for-workflow-agents-with-approval-points-2026-recommendations/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.sphereinc.com/blogs/how-to-evaluate-ai-agents-in-2026 |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/jackm-singularity/ai-agent-runtime-policy-stop-dangerous-tool-calls-before-they-execute-4hp4 |

### 2.2.2

**Q:** Policy language and decision engine (OPA / Cedar / other); is the decision point behind a standard query interface (e.g. OpenID AuthZEN)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-09-03 | exc | cur gpt | cursor:0.1.4 | https://openid.github.io/authzen/ |
| core | B1 | T1 | 2026-09-03 | exc | gpt | — | https://openid.github.io/authzen/authzen-access-request-approval-profile-1_0.html |
| core | B1 | T1 | 2026-09-02 | exc | gpt | — | https://mailarchive.ietf.org/arch/msg/i-d-announce/A5URd3bTKWCHORfvGu8MhPC3Wis/ |
| core | B2 | T1 | 2026-06 | exc | fab | — | https://openid.net/openid-foundation-advances-authorization-for-the-agent-era-with-new-authzen-working-group-drafts/ |
| core | B2 | T1 | 2026-01-12 | exc | fab kim | — | https://openid.net/authorization-api-1-0-final-specification-approved/ |
| core | B2 | T1 | 2026-01-11 | exc | fab kim | — | https://openid.net/specs/authorization-api-1_0.html |
| core | B3 | T1 | — † | — | cur | — | https://gitdocumentatie.logius.nl/publicatie/ftv/adl/1.0.0/ |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/openid/authzen/blob/main/api/authorization-api-1_0.md |
| core | B3 | T1 | — † | — | cur | — | https://logius-standaarden.github.io/authorization-decision-log/ |
| core | B3 | T1 | — † | — | fab gpt | 10.2.3 | https://openid.net/wg/authzen/specifications/ |
| core | B3 | T1 | — † | — | fab | — | https://openid.net/wg/authzen/ |
| core | B3 | T1 | — † | — | fab | — | https://openid.net/notice-of-vote-to-approve-proposed-authorization-api-1-final-specification/ |
| core | B3 | T1 | — † | — | fab | — | https://openid.net/public-review-period-for-proposed-authorization-api-1-final-specification/ |
| core | B3 | T1 | — † | — | fab | — | https://openid.net/authzen-shows-enterprise-readiness-at-gartner-iam-summit/ |
| core | B3 | T1 | — † | — | fab | — | https://openid.net/tag/authzen/ |
| primary | B2 | T2 | 2026-03-27 | exc | fab kim gpt | 10.2.3 | https://github.com/open-policy-agent/opa/issues/8449 |
| primary | B3 | T2 | — † | — | cur | — | https://docs.cerbos.dev/cerbos-hub/audit-log-collection.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/manetu/policyengine/blob/main/docs/docs/reference/access-record.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/manetu/policyengine/blob/main/docs/docs/concepts/audit.md |
| primary | B3 | T2 | — † | — | fab | 10.2.3 | https://github.com/modelcontextprotocol/ext-auth/issues/14 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kanywst/opa-authzen-plugin |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/watsuwo/cedar-agent |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/openfga/openfga/pull/2875 |
| primary | B3 | T2 | — † | — | gpt | — | https://tlowerison.github.io/authzen/reference/authz_engines/opa.html |
| research | B1 | T3 | 2026-09-02 | exc | gpt | — | https://ftp.otenet.gr/doc/internet-drafts/draft-gazitt-oauth-authzen-issuance-01.html |
| research | B3 | T3 | — † | — | kim | — | https://agentic-academy.ai/posts/authzen-authorization-api/ |
| research | B3 | T3 | — † | — | fab kim | 10.2.3 | https://auth0.com/blog/implementing-authzen-guide-openid-authorization-api/ |
| research | B3 | T3 | — † | — | fab | — | https://curity.io/resources/learn/authzen/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/kanywst/i-built-an-opa-plugin-that-turns-it-into-an-authzen-compatible-pdp-i81 |
| WILD | B1 | U | 2026-09-02 | exc | gpt | — | https://mirrors.aliyun.com/ietf/draft-gazitt-oauth-authzen-issuance-01.html |
| WILD | B3 | U | — † | — | fab | 10.2.3 | https://dev.to/kanywst/authzen-authorization-api-10-deep-dive-the-standard-api-that-separates-authorization-decisions-1m2a |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@Zeigeist/authzen-cedar-opa-and-zanzibar-style-fga-f72bd1c51395 |
| WILD | B3 | U | — † | — | fab | 10.2.3 | https://techradar.ic-consult.com/access-management/authzen.html |

### 2.2.3

**Q:** Safety classifiers (injection, toxicity) as pluggable adapters behind one interface?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://developer.meta.com/ai/docs/model-cards-and-prompt-formats/prompt-guard/ |
| primary | B3 | T2 | — † | — | kim | — | https://developer.meta.com/ai/docs/model-cards-and-prompt-formats/llama-guard-4/ |
| primary | B3 | T2 | — † | — | kim | — | https://developers.redhat.com/articles/2025/08/26/implement-ai-safeguards-python-and-llama-stack |
| primary | B3 | T2 | — † | — | cur | — | https://docs.agentos.sh/extensions/built-in/ml-classifiers |
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/guardrail-classifiers/latest/guardrail_classifiers/classifier/index.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/framerslab/agentos-extensions/blob/master/registry/curated/safety/ml-classifiers/src/IContentClassifier.ts |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/nexu-io/harness-engineering-guide/blob/main/guide/classifier-permissions.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/meta-llama/PurpleLlama/blob/main/Llama-Prompt-Guard-2/86M/MODEL_CARD.md |
| research | B2 | T3 | 2026 | url | fab kim | — | https://www.digitalapplied.com/blog/llm-guardrails-production-safety-layers-reference-2026 |
| research | B2 | T3 | 2026 | exc | fab kim | — | https://www.morphllm.com/llm-guardrails |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.29659 |
| research | B3 | T3 | 2025-05 | url | fab | — | https://arxiv.org/pdf/2505.03574 |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2605.05277 |
| research | B3 | T3 | — † | — | cur | — | https://awstip.com/stop-reinventing-ai-guardrails-build-reusable-llm-text-safety-with-the-builder-pattern-a238ed4011eb |
| research | B3 | T3 | — † | — | kim | — | https://clickhouse.com/resources/engineering/llm-guardrails |
| research | B3 | T3 | — † | — | fab | — | https://www.wiz.io/academy/ai-security/ai-guardrails |
| WILD | B2 | U | 2026 | exc | fab | — | https://aisecurityandsafety.org/en/guides/llm-guardrails/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://cowork.ink/blog/ai-agent-guardrails/ |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/ultimate-guide-llm-guardrails-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.getmaxim.ai/articles/the-complete-ai-guardrails-implementation-guide-for-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://techjacksolutions.com/ai-tools/meta-llama/mastering-llama-safety-and-guardrails/ |
| WILD | B3 | U | — † | — | fab | — | https://aimultiple.com/ai-guardrails |
| WILD | B3 | U | — † | — | fab | — | https://www.solulab.com/llm-guardrails/ |
| WILD | B3 | U | — † | — | kim | — | https://www.trigguardai.com/benchmarks |

### 2.2.4

**Q:** Budgets: who decrements, and what happens on exhaustion mid-run?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab kim | — | https://commandline.microsoft.com/tokenops-real-time-run-scoped-cost-control-ai-agents/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.everruns.com/advanced/budgets/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.litellm.ai/docs/proxy/users |
| primary | B3 | T2 | — † | — | fab | — | https://docs.litellm.ai/docs/a2a_iteration_budgets |
| primary | B3 | T2 | — † | — | fab | — | https://docs.litellm.ai/docs/proxy/provider_budget_routing |
| primary | B3 | T2 | — † | — | fab | — | https://docs.litellm.ai/release_notes/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/calybris-core/latest/src/calybris_core/budget.rs.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/noether-engine/latest/src/noether_engine/executor/budget.rs.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/amabito/veronica-core |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/agenwatch/agenwatch |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/BerriAI/litellm/issues/27923 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/BerriAI/litellm/issues/26672 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/theagentplane/tokenops/blob/main/docs/product/shared-ledger.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/theagentplane/tokenops/blob/main/docs/architecture.md |
| primary | B3 | T2 | — † | — | cur | — | https://pypi.org/project/llm-leash/ |
| research | B2 | T3 | 2026-06 | url | cur | — | https://arxiv.org/html/2606.04056v1 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.04056 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.04056 |
| research | B3 | T3 | — † | — | kim | — | https://runcycles.io/blog/ai-agent-cost-management-guide |
| research | B3 | T3 | — † | — | kim | — | https://runcycles.io/blog/ai-agent-failures-budget-controls-prevent |
| research | B3 | T3 | — † | — | kim | 10.4.1 | https://solana.garden/guides/llm-agent-cost-attribution-token-accounting-explained/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://markaicode.com/pricing/litellm-pricing-gateway-comparison/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.nexgismo.com/blog/ai-agent-budget-guards-stop-runaway-api-costs |
| WILD | B2 | U | 2026 | exc | fab | 10.3.4 10.4.4 | https://waxell.ai/blog/ai-agent-token-budget-enforcement |
| WILD | B3 | U | — † | — | fab | — | https://ai-tldr.dev/releases/litellm-v1-100-0/ |
| WILD | B3 | U | — † | — | fab | — | https://www.almtoolbox.com/blog/litellm-ai-gateway-cost-tracking-guardrails-budgets/ |
| WILD | B3 | U | — † | — | fab | 10.4.4 | https://portal26.ai/ai-agent-cost-control-stop-agents-burning-budget/ |
| WILD | B3 | U | — † | — | fab | — | https://www.trustgateai.io/blog/token-bill-runaway-agents |

### 2.2.5

**Q:** Every decision logged with inputs and policy version?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://docs.styra.com/das/observability-and-audit/decision-logs/overview |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/open-policy-agent/opa/issues/1089 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/microsoft/agent-governance-toolkit/discussions/276 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/open-policy-agent/opa/blob/main/v1/plugins/logs/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/open-policy-agent/opa/pull/7793 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/open-policy-agent/opa/issues/7131 |
| primary | B3 | T2 | — † | — | fab | — | https://www.openpolicyagent.org/docs/management-decision-logs |
| primary | B3 | T2 | — † | — | fab | — | https://openpolicyagent.org/docs/v0.29.4/management-decision-logs |
| primary | B3 | T2 | — † | — | fab | — | https://www.openpolicyagent.org/docs/v0.29.4/management-decision-logs/ |
| primary | B3 | T2 | — † | — | fab | — | https://www.openpolicyagent.org/docs/v0.18.0/management/ |
| primary | B3 | T2 | — † | — | kim | — | https://openpolicyagent.org/docs/management-decision-logs |
| primary | B3 | T2 | — † | — | fab | — | https://pkg.go.dev/github.com/open-policy-agent/opa/v1/plugins/logs |
| primary | B3 | T2 | — † | — | fab | — | https://pkg.go.dev/github.com/open-policy-agent/opa/plugins/logs |
| research | B2 | T3 | 2026-01-28 | url | fab kim | — | https://oneuptime.com/blog/post/2026-01-28-monitor-opa-policy-decisions/view |
| research | B3 | T3 | — † | — | kim | — | https://hoop.dev/blog/auditing-accountability-in-open-policy-agent-opa-best-practices-and-implementation/ |
| research | B3 | T3 | — † | — | kim | — | https://hoop.dev/blog/auditing-open-policy-agent-how-to-log-monitor-and-trust-every-decision/ |
| research | B3 | T3 | — † | — | kim | — | https://orca.security/resources/blog/what-is-open-policy-agent/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://cloudmatos.ai/blog/cedar-best-practices-vs-opa-rego-dlp/ |
| WILD | B3 | U | — † | — | fab | — | https://www.emergentmind.com/topics/policy-decision-record |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/glossary/structured-decision-log/ |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/glossary/decision-log/ |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/faq/how-should-security-teams-monitor-policy-decisions-from-opa-in-production/ |

### 2.2.6

**Q:** Human override mid-run: can an authorized human pause, interrupt, or override a running job via the workflow signal operation (2.4.1), not only at planned gates (2.3.4) or admission (5.2.1); who holds that authority; is the action logged as a policy decision (2.2.5)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab kim gpt | 5.2.1 | https://docs.ag-ui.com/concepts/interrupts |
| primary | B3 | T2 | — † | — | fab | — | https://docs.copilotkit.ai/deepagents/human-in-the-loop/useInterrupt |
| primary | B3 | T2 | — † | — | kim | — | https://docs.langchain.com/oss/python/langgraph/interrupts |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.temporal.io/ai-cookbook/human-in-the-loop-python |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/ai/cookbook/human-in-the-loop-python |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/temporal-community/durable-hitl-agents |
| primary | B3 | T2 | — † | — | fab kim | — | https://learn.temporal.io/tutorials/ai/building-durable-ai-applications/human-in-the-loop/ |
| primary | B3 | T2 | — † | — | fab | — | https://learn.temporal.io/tutorials/ai/building-mcp-tools-with-temporal/adding-hitl-to-mcp-tools/ |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/blog/temporal-langgraph-plugin-durable-execution |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/blog/durable-flexible-multi-agent-systems |
| research | B1 | T3 | 2026-07 | url | fab | 4.3.1 | https://arxiv.org/pdf/2607.08740 |
| research | B1 | T3 | 2026-06-24 | url | kim | — | https://dreaming.press/posts/2026-06-24-how-to-add-human-in-the-loop-to-an-ai-agent.html |
| research | B3 | T3 | — † | — | kim | — | https://www.agentnotebook.dev/tutorials/langgraph-human-in-the-loop |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/royalpinto007/pausing-a-langgraph-agent-mid-run-for-a-human-approval-3nde |
| research | B3 | T3 | — † | — | fab | 2.3.4 4.3.7 | https://www.scalekit.com/blog/human-in-the-loop-tool-calling |
| research | B3 | T3 | — † | — | fab | — | https://www.sweet.security/agent-security/human-oversight-for-ai-agents |
| research | B3 | T3 | — † | — | kim | — | https://www.systemshardening.com/articles/ai-landscape/ai-agent-kill-switches/ |
| WILD | B3 | U | — † | — | fab | — | https://www.abstractalgorithms.dev/langgraph-human-in-the-loop |
| WILD | B3 | U | — † | — | fab | — | https://www.channel.tel/blog/agent-interrupt-checkpoint-approval-patterns |
| WILD | B3 | U | — † | — | fab | — | https://growwstacks.com/blog/human-in-the-loop-ai-agents-temporal |
| WILD | B3 | U | — † | — | fab | — | https://iamstackwell.com/posts/ai-agent-human-override/ |
| WILD | B3 | U | — † | — | fab | — | https://inferensys.com/glossary/enterprise-artificial-intelligence-governance/human-oversight-mechanisms/override-mechanism |
| WILD | B3 | U | — † | — | fab | — | https://uvik.net/blog/human-in-the-loop-ai/ |

### 2.3.1

**Q:** Pattern catalog: single agent, supervisor, swarm, DAG, human-in-loop — declared where?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://agentflow.10xscale.ai/docs/concepts/state-graph |
| primary | B3 | T2 | — † | — | cur | — | https://docs.agent-swarm.dev/docs/concepts/workflows |
| primary | B3 | T2 | — † | — | cur | — | https://docs.agentos.sh/features/workflow-dsl |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/kyegomez/swarms/blob/master/docs/MULTI_AGENT_STRUCTURES.md |
| primary | B3 | T2 | — † | — | cur | — | https://learn.microsoft.com/en-us/agent-framework/workflows/workflows |
| primary | B3 | T2 | — † | — | cur | — | https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/declarative-workflows/advanced-patterns |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns |
| research | B2 | T3 | 2026-01 | url | kim | — | https://arxiv.org/pdf/2601.13671 |
| research | B3 | T3 | 2025-10 | url | fab | — | https://arxiv.org/pdf/2510.24937 |
| research | B3 | T3 | 2025-08 | url | fab | — | https://arxiv.org/pdf/2508.12683 |
| research | B3 | T3 | — † | — | kim | — | https://www.augmentcode.com/guides/swarm-vs-supervisor |
| research | B3 | T3 | — † | — | kim | — | https://cordum.io/blog/multi-agent-system-governance |
| research | B3 | T3 | — † | — | kim | — | https://dattasable.com/blog/architecting-production-multi-agent-ai-systems |
| research | B3 | T3 | — † | — | kim | — | https://doi.org/10.48550/arxiv.2602.16873 |
| research | B3 | T3 | — † | — | kim | — | https://minbook.dev/en/blog/multi-agent-workflow-patterns/ |
| research | B3 | T3 | — † | — | kim | — | https://muhammadamal.my.id/blog/multi-agent-systems-in-2025-architecture-patterns-that-work/ |
| research | B3 | T3 | — † | — | kim | — | https://tyk.io/learning-center/ai-agent-orchestration-a-complete-enterprise-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://www.aihandbook.io/guides/building-agent-swarms/ |
| WILD | B3 | U | — † | — | fab | — | https://www.developersdigest.tech/blog/seven-ai-agent-orchestration-patterns |
| WILD | B3 | U | — † | — | fab | — | https://gurusup.com/blog/agent-orchestration-patterns |
| WILD | B3 | U | — † | — | fab | — | https://harnessengineering.academy/blog/building-multi-agent-orchestration-systems-design-patterns/ |
| WILD | B3 | U | — † | — | fab | — | https://munderdiffl.in/blog/multi-agent-orchestration-patterns/ |

### 2.3.2

**Q:** Plan representation: serializable artifact? No standard exists — what is the platform-owned schema?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B2 | T2 | 2026-05-17 | exc | cur | — | https://taprun.dev/spec/plan-v1/ |
| primary | B3 | T2 | — † | — | cur | — | https://benefitplanstandard.org/docs/specification/field-definitions |
| primary | B3 | T2 | — † | — | cur | — | https://benefitplanstandard.org/docs/getting-started/installation |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Benefit-Plan-Standard/benefit-plan-schema/blob/main/README.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/RetireGolden/RetireGolden/blob/main/DOCS/features/plan-file-format.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ProviderProtocol/agents/blob/5c6a128286d6bfa249e6da183381f66a2be30c64/src/execution/plan.ts |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/JSON-Agents/Standard/blob/main/json-agents.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ddse-foundation/acm/blob/main/spec/acm-spec%20v0.5.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/verivus-oss/agent-assurance/blob/main/spec.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/terrene-foundation/kailash-py/blob/main/workspaces/_archive/kaizen-l3/briefs/05-plan-dag.md |
| primary | B3 | T2 | — † | — | kim | — | https://open-multi-agent.com/reference/plan-replay/ |
| research | B1 | T3 | 2026-08 | url | fab | — | https://arxiv.org/html/2608.13612 |
| research | B1 | T3 | 2026-08 | url | fab | — | https://arxiv.org/html/2608.04661 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.29927 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.18747 |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/html/2604.12147v1 |
| research | B2 | T3 | 2026-04-17 | url | kim | — | https://tianpan.co/blog/2026/04/17/agent-planning-layer-tracing-observability |
| research | B3 | T3 | 2025-12 | url | fab | — | https://arxiv.org/pdf/2512.09629 |
| research | B3 | T3 | 2025-09 | url | fab kim | 2.3.3 2.3.4 | https://arxiv.org/pdf/2509.08646 |
| research | B3 | T3 | 2025-07 | url | fab | — | https://arxiv.org/pdf/2507.02253 |
| research | B3 | T3 | — † | — | fab kim | 3.1.1 | https://www.truefoundry.com/blog/llm-structured-outputs-json-schema |
| WILD | B1 | U | 2026-06-17 | url | fab | — | https://sakul-learning.github.io/2026/06/17/visual-plan-builderio/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/blog/llm-agent-architectures-core-components/ |
| WILD | B2 | U | 2026 | exc | fab | 2.4.3 3.1.1 3.1.2 3.1.3 3.1.5 3.1.6 8.4.1 | https://gist.github.com/amazingvince/52158d00fb8b3ba1b8476bc62bb562e3 |
| WILD | B2 | U | 2026 | exc | fab | 2.3.3 2.4.3 3.4.1 7.1.1 | https://github.com/VoltAgent/awesome-ai-agent-papers |
| WILD | B3 | U | — † | — | kim | — | https://deepwiki.com/eabait/product-agents/8.3-plan-graph-schema |
| WILD | B3 | U | — † | — | kim | — | https://deepwiki.com/agentclientprotocol/agent-client-protocol/2.7-agent-plans |
| WILD | B3 | U | — † | — | fab | — | https://www.emergentmind.com/topics/planner-executor-agentic-framework |

### 2.3.3

**Q:** Planner is a model call, code, or both?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://agentbuilder.readthedocs.io/en/latest/api/planner.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.agentos.sh/features/planning-engine |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/trpc-group/trpc-agent-go/blob/main/docs/mkdocs/en/planner.md |
| research | B1 | T3 | 2026-07-15 | url | cur | — | https://asp.net-hacker.rocks/2026/07/15/ai-planner-orchestrator-pattern.html |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.27806 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/html/2605.21902 |
| research | B3 | T3 | 2025-07 | url | fab | — | https://arxiv.org/pdf/2507.07115 |
| research | B3 | T3 | 2025-07 | url | fab | — | https://arxiv.org/pdf/2507.23589 |
| research | B3 | T3 | 2025-03 | url | fab | — | https://arxiv.org/pdf/2503.24047 |
| research | B3 | T3 | 2024-05 | url | fab | — | https://arxiv.org/pdf/2405.01453 |
| research | B3 | T3 | 2023-09 | url | fab | — | https://arxiv.org/pdf/2309.02427 |
| research | B3 | T3 | — † | — | kim | — | https://hackernoon.com/designing-reliable-llm-agents-with-deterministic-control-flow |
| research | B3 | T3 | — † | — | kim | — | https://www.langchain.com/blog/planning-agents |
| research | B3 | T3 | — † | — | kim | — | https://mastra.ai/articles/ai-agent-architecture |
| research | B3 | T3 | — † | — | cur | — | https://medium.com/@servifyspheresolutions/planner-executor-critic-engineering-reliable-ai-agents-4eed3b5ddb54 |
| research | B3 | T3 | — † | — | kim | — | https://mortalapps.com/agents/architecture-patterns/plan-and-execute-agent-architecture/ |
| research | B3 | T3 | — † | — | kim | — | https://www.reddit.com/r/AI_Agents/comments/1udp99l/the_most_reliable_data_agent_ive_shipped_is_90/ |
| research | B3 | T3 | — † | — | kim | — | https://suhasbhairav.com/blog/planner-executor-agents-vs-react-agents-upfront-task-decomposition-vs-iterative-reason-act-loops |
| WILD | B2 | U | 2026 | url | fab | — | https://hugobowne.substack.com/p/llm-architecture-in-2026-agent-harnesses |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Planning-Tasks |
| WILD | B3 | U | — † | — | fab | — | https://www.emergentmind.com/topics/llm-planner-agent |
| WILD | B3 | U | — † | — | kim | — | https://www.youtube.com/watch?v=0fH-tWLvDC4 |

### 2.3.4

**Q:** Approval gates and replanning triggers.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Smithbox-ai/ControlFlow/blob/master/Orchestrator.agent.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Smithbox-ai/ControlFlow/blob/master/docs/tutorial-en/05-orchestration.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/mkurman/tamux/blob/HEAD/docs/goal-runners.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Smithbox-ai/ControlFlow/blob/master/docs/agent-engineering/RELIABILITY-GATES.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Smithbox-ai/ControlFlow/blob/master/docs/tutorial-en/13-failure-taxonomy.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/bryanyzhu/agentic-ai-system-course/blob/main/course/09-planning-patterns.md |
| primary | B3 | T2 | — † | — | kim | — | https://open-multi-agent.com/reference/adaptive-recovery/ |
| research | B1 | T3 | 2026-09-02 | url | gpt | — | https://opcreport.github.io/2026/09/02/opc-report-2026-09-02-1126/ |
| research | B2 | T3 | 2026-06 | url | cur | — | https://ar5iv.labs.arxiv.org/html/2606.20058 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.24309 |
| research | B2 | T3 | 2026-04 | url | fab | 2.4.5 7.2.2 | https://arxiv.org/pdf/2604.08224 |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.03581 |
| research | B3 | T3 | — † | — | kim | — | https://adpsagent.com/patterns/a2-plan-and-execute/ |
| research | B3 | T3 | — † | — | cur kim | 5.1.4 | https://www.agentpatternscatalog.org/patterns/replan-on-failure/ |
| research | B3 | T3 | — † | — | kim | — | https://arunbaby.com/ai-agents/0040-hierarchical-planning/ |
| research | B3 | T3 | — † | — | kim | — | https://dvnc.dev/blog/human-approval-gates-ai-agents |
| research | B3 | T3 | — † | — | cur | — | https://www.stackai.com/insights/human-in-the-loop-ai-agents-how-to-design-approval-workflows-for-safe-and-scalable-automation |
| research | B3 | T3 | — † | — | kim | — | https://www.velsof.com/ai-automation/ai-agent-replanning-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.automationanywhere.com/rpa/agentic-workflows |
| WILD | B2 | U | 2026 | url | fab | — | https://explainx.ai/blog/human-in-the-loop-ai-when-to-let-agent-run-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://getclaw.sh/blog/human-in-the-loop-ai-agents-approvals-2026 |
| WILD | B2 | U | 2026-05-14 | url | fab | — | https://zylos.ai/research/2026-05-14-long-horizon-planning-goal-decomposition-ai-agents/ |
| WILD | B2 | U | 2026-04 | url | fab | — | https://fazm.ai/t/llm-agents-news-april-2026 |
| WILD | B2 | U | 2026-04 | url | fab | — | https://fazm.ai/blog/new-llm-releases-april-2026 |
| WILD | B3 | U | — † | — | fab | — | https://createos.sh/blogs/human-in-the-loop-ai-agents |

### 2.4.1

**Q:** The port over the workflow engine: which operations does the platform need (start, signal, query, cancel, await)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.temporal.io/sending-messages |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/cli/workflow |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/java/message-passing |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/python/message-passing |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/handling-messages |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/go/message-passing |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/encyclopedia/workflow-message-passing |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/evaluate/development-production-features/workflow-message-passing |
| primary | B3 | T2 | — † | — | kim | — | https://docs.temporal.io/develop/typescript/client/temporal-client |
| primary | B3 | T2 | — † | — | kim | — | https://docs.temporal.io/develop/typescript/workflows/message-passing |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/TanStack/workflow/blob/main/docs/overview.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/duroxide/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/danthegoodman1/durust |
| primary | B3 | T2 | — † | — | fab | — | https://pkg.go.dev/go.temporal.io/sdk/workflow |
| primary | B3 | T2 | — † | — | cur kim | cursor:2.5.1 | https://typescript.temporal.io/api/interfaces/client.WorkflowHandle |
| primary | B3 | T2 | — † | — | kim | — | https://typescript.temporal.io/api/classes/client.WorkflowClient |
| research | B2 | T3 | 2026-02-03 | url | fab | — | https://james-carr.org/posts/2026-02-03-temporal-process-manager/ |
| research | B3 | T3 | 2022-04 | url | fab | — | https://arxiv.org/pdf/2204.07210 |
| WILD | B3 | U | — † | — | kim | — | https://github.com/satadeep3927/loom |

### 2.4.2

**Q:** Definition portability: engine-native code (Temporal SDK) vs declarative spec (CNCF Serverless Workflow, BPMN). Exit cost of each?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | — | https://www.cncf.io/projects/serverless-workflow/ |
| core | B3 | T1 | — † | — | kim | — | https://github.com/serverlessworkflow/specification/issues/1149 |
| core | B3 | T1 | — † | — | fab | — | https://insights.linuxfoundation.org/project/serverlessworkflow |
| core | B3 | T1 | — † | — | fab | — | https://serverlessworkflow.io/ |
| primary | B1 | T2 | 2026-08-06 | exc | gpt | — | https://temporal.io/changelog/product-area/server |
| primary | B1 | T2 | 2026-07-18 | exc | fab | — | https://eventmesh.apache.org/blog/cncf-serverlessworkflow-official-recommends-eventmesh-as-runtime-impl/ |
| primary | B3 | T2 | — † | — | fab | — | https://community.temporal.io/t/temporal-integrtaion-with-serverless-workflow-with-type-script-sdk/10260 |
| primary | B3 | T2 | — † | — | fab | — | https://docs.kuberkai.com/concepts/serverless-workflow-spec/ |
| primary | B3 | T2 | — † | — | fab kim | 2.4.7 | https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/evaluate/serverless-workers |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/serverlessworkflow/editor |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/zigflow/zigflow/blob/main/docs/docs/concepts/comparing-zigflow-and-temporal-sdks.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/temporalio/skill-temporal-serverless/blob/main/SKILL.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/temporalio/temporal/releases |
| primary | B3 | T2 | — † | — | fab | — | https://kiegroup.github.io/kogito-docs/serverlessworkflow/1.31.1.Final/getting-started/cncf-serverless-workflow-specification-support.html |
| primary | B3 | T2 | — † | — | fab | — | https://sonataflow.org/serverlessworkflow/latest/core/cncf-serverless-workflow-specification-support.html |
| research | B2 | T3 | 2026 | url | fab kim | — | https://automationatlas.io/guides/camunda-vs-temporal-2026-comparison/ |
| research | B2 | T3 | 2026-03-24 | exc | gpt | — | https://jdriven.com/blog/2026/03/Battle-testing-Temporal-Part-1 |
| research | B3 | T3 | 2022-05-15 | url | cur fab | cursor:2.5.2 | https://blog.automatiko.io/2022/05/15/serverless-vs-bpmn.html |
| research | B3 | T3 | — † | — | fab kim | — | https://gillesbarbier.medium.com/understanding-the-serverless-workflow-1-0-dsl-6e874a1fd511 |
| research | B3 | T3 | — † | — | kim | — | https://know.2nth.ai/explainers/biz/bpm/process-orchestration |
| research | B3 | T3 | — † | — | kim | — | https://www.linkedin.com/pulse/we-partner-both-camunda-8-temporal-heres-which-one-wed-piotr-zawadzki-q4ybf |
| research | B3 | T3 | — † | — | fab | — | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8270184/ |
| research | B3 | T3 | — † | — | kim | — | https://quantumbpm.com/blog/bpmn-vs-temporal |
| WILD | B2 | U | 2026 | exc | fab | — | https://checkthat.ai/brands/temporal/pricing |
| WILD | B3 | U | 2025 | url | fab | — | https://tasrieit.com/blog/top-10-workflow-automation-open-source-tools-2025 |
| WILD | B3 | U | 2020-12-16 | exc | fab | — | https://data.epo.org/gpi/EP3750061A1 |
| WILD | B3 | U | — † | — | fab | — | https://akka.io/blog/temporal-alternatives |
| WILD | B3 | U | — † | — | fab | — | https://github.com/serverless-workflow/workflow-bpmn |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/tsurdilo/swtemporal |

### 2.4.3

**Q:** How does a plan (2.3) compile into a workflow without engine-specific constructs?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://conductor-oss.github.io/conductor/devguide/ai/dynamic-workflows.html |
| primary | B3 | T2 | — † | — | kim | — | https://conductor-oss.github.io/conductor/architecture/json-native.html |
| primary | B3 | T2 | — † | — | kim | 4.3.2 | https://docs.temporal.io/develop/python/integrations/langgraph |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/droidraja/zigflow/blob/a3459431/DYNAMIC_WORKFLOW_EXECUTION_PLAN.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mattapperson/noetic/commit/436f57a51fc44f34e92b586e7e3bfe130ca62129 |
| primary | B3 | T2 | — † | — | kim | — | https://pypi.org/project/adk-dynamic-workflows/ |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/pages/durable-ai-agent-bundle |
| research | B1 | T3 | 2026-09 | url | fab | — | https://arxiv.org/html/2609.06128 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/html/2605.15215v1 |
| research | B2 | T3 | 2026-05 | url | kim | — | https://www.infoq.com/news/2026/05/cloudflare-dynamic-workflows/ |
| WILD | B1 | U | 2026-06-29 | url | fab | — | https://niteagent.com/blog/2026-06-29-durable-ai-agents-temporal-guide/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.futureproofing.dev/resources/ai-native-team/agentic-coding-workflow-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://olmecdynamics.com/news/temporal-durable-execution-agentic-workflows-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.reactify-solutions.com/articles/durable-ai-agents-2026 |
| WILD | B3 | U | 2025-07-30 | url | fab | — | https://www.businesswire.com/news/home/20250730783559/en/Temporal-and-OpenAI-Launch-Integration-for-Enterprises-Developing-Production-Agents |
| WILD | B3 | U | — † | — | fab | — | https://www.antoinebuteau.com/agents-should-compile-workflows-not-replay-them/ |
| WILD | B3 | U | — † | — | fab | — | https://blakecrosley.com/blog/agents-want-to-compile |
| WILD | B3 | U | — † | — | kim | — | https://deepwiki.com/droidraja/zigflow/3.4-dynamic-workflow-execution |
| WILD | B3 | U | — † | — | fab | — | https://fredk8.dev/blog/durable-ai-agents-orchestrating-the-future-with-fred-and-temporal/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/durable-execution?l=go&o=asc&s=updated |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12437238 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12430150 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12566913 |

### 2.4.4

**Q:** Does the engine own schedules (1.2), or does it consume them as events (1.3)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.temporal.io/develop/python/workflows/schedules |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.temporal.io/develop/go/workflows/schedules |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/java/workflows/schedules |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/cron-job |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/cli/schedule |
| primary | B3 | T2 | — † | — | fab | 2.4.6 | https://temporal.io/product |
| research | B3 | T3 | — † | — | kim | — | https://devpath-traveler.nguyenviettung.id.vn/cron-vs-queue-vs-event-choosing-the-right-trigger |
| research | B3 | T3 | — † | — | kim | — | https://www.nilus.be/blog/workflow_engines_vs_event_pipelines_in_microservices/ |
| research | B3 | T3 | — † | — | kim | — | https://unstructured.io/insights/event-driven-vs-scheduled-workflows-for-ai-data-pipelines |
| research | B3 | T3 | — † | — | fab | — | https://www.zenml.io/blog/temporal-vs-airflow |
| WILD | B2 | U | 2026 | exc | fab | — | https://automationatlas.io/answers/what-is-workflow-engine/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://mlai.qa/blog/temporal-vs-airflow/ |
| WILD | B3 | U | — † | — | fab | — | https://blog.damavis.com/en/airflow-3-scheduling-timetables-assets-and-event-driven-pipelines/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11611519 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11157882 |
| WILD | B3 | U | — † | — | fab | 2.4.6 | https://www.kunalganglani.com/blog/temporal-workflow-engine-guide |
| WILD | B3 | U | — † | — | fab | — | https://registry.terraform.io/providers/rest-capital/temporal-schedules/latest/docs/resources/schedule |

### 2.4.5

**Q:** Handoff to the worker: internal contract, or A2A (1.5) even in-cluster?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-08-27 | url | gpt | — | https://a2a-protocol.org/dev/blog/2026/08/27/a-new-chapter-for-a2a-joining-the-agentic-ai-foundation/ |
| core | B2 | T1 | 2026-04 | exc | fab | — | https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year |
| core | B3 | T1 | 2025-06-23 | exc | cur fab | cursor:9.3.2 | https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents |
| core | B3 | T1 | — † | — | gpt | — | https://a2a-protocol.org/v1.0.0/ |
| primary | B2 | T2 | 2026-04 | url | fab | — | https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html |
| primary | B3 | T2 | — † | — | fab | — | https://developers.googleblog.com/en/google-cloud-donates-a2a-to-linux-foundation/ |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.a2acloud.io/platform/agents |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.conductor-oss.org/devguide/ai/cookbook/a2a-orchestration.html |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.conductor-oss.org/devguide/ai/a2a-integration.html |
| research | B1 | T3 | 2026-07-06 | exc | gpt | — | https://agentsurface.dev/docs/protocols/a2a |
| research | B2 | T3 | 2026 | url | gpt | — | https://essamamdani.com/blog/complete-guide-a2a-protocol-2026 |
| research | B2 | T3 | 2026 | url | fab kim | 9.2 | https://rapidclaw.dev/blog/a2a-protocol-complete-guide-2026 |
| research | B2 | T3 | 2026-03-15 | url | gpt | — | https://mcpblog.dev/blog/2026-03-15-a2a-v1-mcp |
| research | B3 | T3 | — † | — | gpt | — | https://a2acloud.io/multi-agent-orchestration |
| research | B3 | T3 | — † | — | kim | — | https://cloudrps.com/blog/a2a-agent-to-agent-protocol-cloud-infrastructure/ |
| research | B3 | T3 | — † | — | kim | — | https://www.knowlee.ai/blog/multi-agent-communication-protocols-mcp-a2a |
| research | B3 | T3 | — † | — | cur kim | 9.3 cursor:9.1.3 cursor:9.4.3 | https://mattgoodrich.com/posts/agent-communication-stack/ |
| research | B3 | T3 | — † | — | kim | — | https://nitinksingh.com/posts/multi-agent-architecture-orchestration-and-the-a2a-protocol/ |
| research | B3 | T3 | — † | — | kim | — | https://redis.io/blog/when-does-a2a-protocol-matter/ |
| research | B3 | T3 | — † | — | kim | — | https://www.spheron.network/blog/deploy-a2a-agent2agent-multi-agent-gpu-cloud/ |
| research | B3 | T3 | — † | — | kim | — | https://swarmsignal.net/mcp-vs-a2a-vs-acp-agent-protocol-comparison/ |
| WILD | B2 | U | 2026 | url | fab | — | https://agora-intelligence.com/en/blog/leon-a2a-protocol-production-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://devtoollab.com/blog/a2a-protocol-guide-2026 |
| WILD | B2 | U | 2026-02-28 | age | gpt | — | https://www.reddit.com/r/LocalLLaMA/comments/1rhfrvi/removed/ |
| WILD | B3 | U | — † | — | kim | — | https://aeef.ai/reference-implementations/orchestration/a2a-progressive-adoption-guide |
| WILD | B3 | U | — † | — | fab | — | https://mastra.ai/blog/what-is-agent-to-agent-protocol |
| WILD | B3 | U | — † | — | fab | — | https://www.mindstudio.ai/blog/what-is-a2a-agent-to-agent-protocol |
| WILD | B3 | U | — † | — | fab | — | https://www.prnewswire.com/news-releases/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year-302737641.html |
| WILD | B3 | U | — † | — | fab | — | https://www.salesforce.com/agentforce/ai-agents/agent2agent-protocol/ |
| WILD | B3 | U | — † | — | fab | — | https://stellagent.ai/insights/a2a-protocol-google-agent-to-agent |

### 2.4.6

**Q:** Cancellation, timeouts, and compensation semantics.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://cadenceworkflow.io/docs/concepts/activities |
| primary | B3 | T2 | — † | — | fab | — | https://community.temporal.io/t/workflow-timeout-and-saga-compensation/8377 |
| primary | B3 | T2 | — † | — | fab | — | https://community.temporal.io/t/passing-parameters-dynamically-to-saga-compensation-activities/6456 |
| primary | B3 | T2 | — † | — | fab | — | https://community.temporal.io/t/saga-compensate-vs-workflow-cancellationscope/1297 |
| primary | B3 | T2 | — † | — | kim | — | https://conductor-oss.github.io/conductor/devguide/cookbook/saga-compensation.html |
| primary | B3 | T2 | — † | — | cur kim | — | https://docs.temporal.io/design-patterns/saga-pattern |
| primary | B3 | T2 | — † | — | cur | — | https://docs.temporal.io/develop/java/workflows/cancellation |
| primary | B3 | T2 | — † | — | kim | — | https://docs.temporal.io/guides/saga-pattern |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/temporal-sa/validated-pattern-keep-business-moving |
| primary | B3 | T2 | — † | — | cur | — | https://python.durable-workflow.com/reference/workflow/ |
| primary | B3 | T2 | — † | — | cur fab | — | https://temporal.io/blog/compensating-actions-part-of-a-complete-breakfast-with-sagas |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/blog/keep-business-processes-moving |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/blog/temporal-replaces-state-machines-for-distributed-applications |
| research | B1 | T3 | 2026-07 | exc | fab kim | — | https://hosseinnejati.medium.com/implementing-the-saga-pattern-with-temporal-compensation-without-the-complexity-2000edbf07c5 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.17182 |
| research | B2 | T3 | 2026-02 | url | fab kim | 3.4.4 10.3.1 | https://arxiv.org/pdf/2602.14849 |
| research | B2 | T3 | 2026-01-29 | url | fab | — | https://james-carr.org/posts/2026-01-29-temporal-workflow-orchestration/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/gabrielanhaia/saga-timeouts-the-compensation-path-most-teams-never-test-1dok |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/mashhadi/the-provider-timed-out-after-committing-101g |
| research | B3 | T3 | — † | — | kim | — | https://hld.handbook.academy/curriculum/distributed-systems-theory/distributed-transactions/ |
| research | B3 | T3 | — † | — | fab | — | https://keithtenzer.com/temporal/Temporal_Fundamentals_Workflow_Patterns/ |
| research | B3 | T3 | — † | — | kim | — | https://mamenesia.com/lessons/0051-saga-compensations/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@sanilkhurana7/system-design-series-the-story-and-present-of-durable-execution-and-how-to-use-it-in-your-52509b94d01e |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@kaushalsinh73/node-js-durable-execution-with-temporal-ts-saga-patterns-without-orchestration-chaos-249132ccf609 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/skyro-tech/solving-distributed-transactions-with-the-saga-pattern-and-temporal-27ccba602833 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@kanhaaggarwal/the-temporal-saga-nightmare-why-your-compensation-steps-never-trigger-45a009f8be2e |

### 2.4.7

**Q:** In-flight workflow upgrade: when workflow code changes, are running instances pinned to their starting version, migrated via engine-native versioning, or drained first?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://docs.mendix.com/refguide/workflow-versioning/ |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.temporal.io/develop/go/workflows/versioning |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/java/versioning |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/java/workflows/versioning |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/typescript/versioning |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/python/workflows/versioning |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/develop/dotnet/workflows/versioning |
| primary | B3 | T2 | — † | — | kim | — | https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning/upgrade-on-continue-as-new |
| primary | B3 | T2 | — † | — | kim | — | https://docs.temporal.io/develop/safe-deployments |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/temporalio/documentation/blob/main/docs/production-deployment/worker-deployments/worker-versioning/index.mdx |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/temporalio/documentation/issues/4433 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/temporalio/documentation/blob/main/docs/production-deployment/worker-deployments/worker-versioning.mdx |
| primary | B3 | T2 | — † | — | fab kim | — | https://temporal.io/blog/ga-worker-versioning-public-preview-upgrade-on-continue-as-new |
| primary | B3 | T2 | — † | — | fab kim | — | https://temporal.io/blog/announcing-worker-versioning-public-preview-pin-workflows-to-a-single-code |
| primary | B3 | T2 | — † | — | fab kim | — | https://temporal.io/blog/safe-deployments-with-temporal-worker-versioning-on-kubernetes |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/changelog/worker-versioning-public-preview |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/blog/automated-worker-versioning-with-github-actions |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/blog/migrating-temporal-workflows-to-aws-lambda |
| WILD | B3 | U | — † | — | fab | — | https://callsphere.ai/blog/workflow-versioning-migration-updating-running-agent-workflows |

### 2.4.8

**Q:** Fan-out width: ceiling on parallel branches a supervisor or planner spawns in one step; enforced by dispatch (2.4) or the scheduler (4.2)? (1.5.3 bounds depth, not width.)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://github.com/openai/codex/issues/39129 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/yonatangross/orchestkit/blob/main/plugins/ork/skills/langgraph/rules/parallel-fanout-fanin.md |
| research | B2 | T3 | 2026 | exc | fab kim | — | https://beam.ai/agentic-insights/multi-agent-orchestration-patterns-production |
| research | B2 | T3 | 2026-04-26 | url | kim | — | https://zylos.ai/research/2026-04-26-parallel-concurrency-agent-execution/ |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.20405 |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2507.06520v1 |
| research | B3 | T3 | — † | — | kim | — | https://forum.langchain.com/t/best-practices-for-parallel-nodes-fanouts/1900 |
| research | B3 | T3 | — † | — | kim | — | https://markaicode.com/langgraph-parallel-fan-out-fan-in/ |
| research | B3 | T3 | — † | — | kim | — | https://pratikdhanave.com/blog/posts/harness-engineering-go-07-hierarchical-supervision.html |
| research | B3 | T3 | — † | — | kim | — | https://pub.towardsai.net/multi-agent-fan-out-when-parallelism-bites-back-c42656dd4d2f |
| research | B3 | T3 | — † | — | kim | — | https://ranjankumar.in/langgraph-multi-agent-fan-out-width-bound |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/claude-code-subagent-depth-limits-budget-caps-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://jobsbyculture.com/blog/ai-agent-orchestration-patterns-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.aibuilderclub.com/blog/claude-code-sub-agents-guide |
| WILD | B3 | U | — † | — | fab | — | https://www.firecrawl.dev/blog/codex-multi-agent-orchestration |
| WILD | B3 | U | — † | — | fab | — | https://hidekazu-konishi.com/entry/claude_code_subagents_and_orchestration_guide.html |
| WILD | B3 | U | — † | — | fab | — | https://www.howardism.dev/articles/parallel-agent-orchestration |
| WILD | B3 | U | — † | — | fab | — | https://ssojet.com/blog/parallel-sub-agent-coding-tools |

### 2.4.9

**Q:** Priority under contention: how is the intake priority field (2.1.3) enforced at dispatch — weighted fair queueing, strict priority with a starvation guard, or per-tenant reservation?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/crate/firq-core/latest |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.temporal.io/develop/task-queue-priority-fairness |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.temporal.io/design-patterns/fairness |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/design-patterns/priority-task-queues |
| primary | B3 | T2 | — † | — | fab | — | https://dotnet.temporal.io/api/Temporalio.Common.Priority.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/anon-000/epoch |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/madmax983/autumn-harvest/pull/391 |
| primary | B3 | T2 | — † | — | fab kim | — | https://temporal.io/blog/task-queue-priority-and-fairness-your-task-queue-your-way |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/change-log/task-queue-priority-fairness-public-preview |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/changelog/priority-fairness-generally-available |
| primary | B3 | T2 | — † | — | fab | — | https://temporal.io/resources/on-demand/announcing-priority-and-fairness-for-temporal |
| primary | B3 | T2 | — † | — | fab | — | https://typescript.temporal.io/api/classes/proto.temporal.api.common.v1.Priority |
| research | B1 | T3 | 2026-08-27 | url | fab | — | https://developers.redhat.com/articles/2026/08/27/llm-d-flow-control-priority-queuing-for-shared-gpu-inference |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.02982 |
| research | B3 | T3 | 2024-01 | url | fab | — | https://arxiv.org/pdf/2401.08890 |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/priority-queue-ai |
| research | B3 | T3 | — † | — | kim | — | https://www.techinterview.org/post/3233468902/lld-priority-queue/ |
| WILD | B3 | U | — † | — | fab | — | https://daily.dev/posts/task-queue-priority-and-fairness-your-task-queue-your-way-oi28edbnk |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/6990115 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9742683 |
| WILD | B3 | U | — † | — | fab | — | https://www.networkacademy.io/ccna/network-services/queuing-and-scheduling |
| WILD | B3 | U | — † | — | fab | — | https://satellitegroundstation.com/resources/conflict-management-priority-queues-fairness-and-reservations/ |

## 3. Core Agent

### 3.1.1

**Q:** What the platform requires of any harness: input/output schema, streaming, tool interface, session, cancellation, resource limits.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-08-11 | exc | kim | — | https://unifiedharnessprotocol.dev/spec/ |
| core | B1 | T1 | 2026-08-11 | exc | kim | — | https://unifiedharnessprotocol.dev/lifecycle/ |
| core | B3 | T1 | — † | — | kim | — | https://unifiedharnessprotocol.org/ |
| primary | B1 | T2 | 2026-08 | age | cur fab kim | 3.4.3 cursor:3.1.5 | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-sessions.html |
| primary | B1 | T2 | 2026-08 | age | cur | — | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html |
| primary | B3 | T2 | — † | — | kim | 4.3.1 | https://github.com/temporal-community/temporal-agent-harness |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-framework/blob/de39be9e/python/packages/core/agent_framework/_harness/_agent.py |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ramannanda9/agent-harness |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/strands-agents/harness-sdk/pull/2360 |
| research | B1 | T3 | 2026-08 | age | cur | — | https://awsfundamentals.com/blog/bedrock-agentcore-harness |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.06906 |
| research | B1 | T3 | 2026-07 | age | cur | — | https://dev.to/aws-heroes/amazon-bedrock-agentcore-runtime-part-1-introduction-e5i |
| research | B2 | T3 | 2026-06 | age | cur | — | https://joudwawad.medium.com/aws-bedrock-agentcore-deep-dive-6822e4071774 |
| research | B3 | T3 | — † | — | fab | — | https://credal.ai/blog/agent-harness-vs-agent-runtime |
| research | B3 | T3 | — † | — | fab | — | https://www.harness.io/blog/harness-mcp-server-redesign |
| WILD | B2 | U | 2026 | url | fab | — | https://agentconn.com/blog/agent-idle-time-billing-durable-execution-2026/ |
| WILD | B2 | U | 2026 | exc | fab | 3.1.3 3.1.5 | https://www.explainx.ai/blog/what-is-agent-harness-complete-guide-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.kunalganglani.com/blog/agent-tool-call-failure-testing |
| WILD | B2 | U | 2026 | exc | fab | 4.3.1 | https://qubittool.com/blog/anatomy-of-agent-harness |
| WILD | B2 | U | 2026-04-07 | url | fab | — | https://agentmarketcap.ai/blog/2026/04/07/agent-streaming-architecture-sse-websocket-http-2026 |

### 3.1.2

**Q:** Does the harness speak the session protocol (1.1) natively? If not, where is the adapter?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur fab kim | — | https://ai-sdk.dev/providers/ai-sdk-harnesses/acp |
| primary | B1 | T2 | 2026-08-26 | url | fab | — | https://code.visualstudio.com/blogs/2026/08/26/agent-host-architecture |
| primary | B1 | T2 | 2026-08-13 | exc | cur | — | https://omidsaffari.com/blog/vercel-ai-sdk-acp-harness-adapter-explained |
| primary | B2 | T2 | 2026 | exc | fab | 3.1.3 3.1.6 | https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-at-build-2026-announce/ |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://vcoderun.github.io/acpkit/pydantic-acp/session-state/ |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://vcoderun.github.io/acpkit/langchain-acp/adapter-config/ |
| primary | B2 | T2 | 2026-01-28 | url | fab | — | https://github.blog/changelog/2026-01-28-acp-support-in-copilot-cli-is-now-in-public-preview/ |
| primary | B3 | T2 | — † | — | fab | — | https://agentclientprotocol.com/get-started/clients |
| primary | B3 | T2 | — † | — | fab | — | https://docs.agent-swarm.dev/docs/guides/harness-providers |
| primary | B3 | T2 | — † | — | kim gpt | — | https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/acp/acp/README.md |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/openclaw/acpx/blob/main/CHANGELOG.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kevin-dp/agent-session-protocol?v=1 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/jensbodal/agents-js/blob/main/docs/harness-guide.md |
| primary | B3 | T2 | — † | — | fab | — | https://www.jetbrains.com/acp/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.npmjs.com/package/agent-session-protocol |
| primary | B3 | T2 | — † | — | gpt | — | https://pkg.go.dev/github.com/webgrip/ploeg/pkg/harness/adapters/acp |
| primary | B3 | T2 | — † | — | kim | — | https://pydantic.dev/docs/ai/harness/acp/ |
| primary | B3 | T2 | — † | — | fab | — | https://zed.dev/acp |
| research | B1 | T3 | 2026-09-10 | exc | gpt | 9.1 9.2 | https://unifiedharnessprotocol.dev/uhp-vs-acp/ |
| research | B1 | T3 | 2026-07 | age | cur gpt | — | https://unifiedharnessprotocol.dev/ai-sdk-harnesses/ |
| research | B1 | T3 | 2026-06-28 | exc | gpt | — | https://frontman.sh/blog/building-agentic-harness-agent-client-protocol/ |
| research | B1 | T3 | 2026-06-14 | url | gpt | — | https://dsh-atlas.vercel.app/notes/archived/feature/2026-06-14-acp-agent-client-protocol |
| research | B3 | T3 | — † | — | kim | — | https://www.agent-native.com/docs/harness-agents |
| research | B3 | T3 | — † | — | fab kim | 3.1.5 | https://aimultiple.com/agent-harness |
| research | B3 | T3 | — † | — | cur fab | cursor:1.1.3 | https://blog.marcnuri.com/agent-client-protocol-acp-introduction |
| research | B3 | T3 | — † | — | gpt | — | https://unifiedharnessprotocol.dev/opencode/ |
| WILD | B3 | U | — † | — | fab | — | https://fossies.org/linux/openclaw/docs/tools/acp-agents.md |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/dennisonbertram/go-code/issues/746 |

### 3.1.3

**Q:** Is the planner (2.3) itself run as a harness job?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B2 | T2 | 2026-04 | exc | kim | — | https://www.anthropic.com/engineering/harness-design-long-running-apps |
| primary | B3 | T2 | — † | — | kim | — | https://docs.swarms.world/api/planner-generator-evaluator |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/suhanlee/harness |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/jason-c-dev/claude-harness |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/JohnsonYe/agents-harness |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/html/2605.18747v1 |
| research | B3 | T3 | — † | — | kim | — | https://www.agentpatternscatalog.org/patterns/planner-generator-evaluator-harness/ |
| research | B3 | T3 | — † | — | kim | — | https://www.mindstudio.ai/blog/planner-generator-evaluator-pattern-gan-inspired-ai-coding |
| research | B3 | T3 | — † | — | kim | — | https://pub.towardsai.net/stop-calling-it-an-agent-anthropic-calls-it-a-harness-4774d5056e7b |
| WILD | B1 | U | 2026-08 | url | fab | — | https://www.infoq.com/news/2026/08/agent-framework-harness-ga/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://explainx.ai/blog/agent-harness-dag-planner-worker-critic-budget-pressure-2026 |
| WILD | B2 | U | 2026 | exc | fab | 3.1.5 | https://winder.ai/ai-agent-harness-comparison/ |
| WILD | B3 | U | — † | — | fab | — | https://blog.whoisjsonapi.com/how-modern-ai-agents-use-harnesses-for-planning-execution-and-recovery/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@ml-point/agent-harness-25c93a8344bf |

### 3.1.4

**Q:** "One per cell": is a cell a container, VM, or process? Who enforces one job per harness?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | 3.1.8 4.1.1 | https://agent-sandbox.sigs.k8s.io/docs/ |
| core | B3 | T1 | — † | — | fab kim | 3.1.8 4.1.2 | https://github.com/kubernetes-sigs/agent-sandbox |
| primary | B2 | T2 | 2026-03-20 | url | kim | — | https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/nexu-io/harness-engineering-guide/blob/main/guide/managed-agents-architecture.md |
| research | B1 | T3 | 2026-08 | age | cur fab kim | 3.3.2 10.1.9 | https://northflank.com/blog/how-to-sandbox-ai-agents |
| research | B2 | T3 | 2026 | exc | fab | 3.5.4 4.1.2 | https://cosmonic.com/blog/ai-sandbox-guide/ |
| research | B2 | T3 | 2026 | exc | fab kim | 3.1.6 | https://www.truefoundry.com/blog/best-agent-harness-in-2026 |
| research | B2 | T3 | 2026-04-09 | url | kim | — | https://tianpan.co/blog/2026-04-09-managed-agents-decoupling-brain-hands |
| research | B3 | T3 | — † | — | kim | — | https://chierhu.medium.com/separating-the-agent-harness-from-compute-b3e559ea4699 |
| research | B3 | T3 | — † | — | kim | — | https://cloudnativenow.com/features/kubernetes-builds-a-sandbox-crd-for-ai-agents/ |
| research | B3 | T3 | — † | — | kim | 3.1.8 | https://northflank.com/blog/agent-sandbox-on-kubernetes |
| research | B3 | T3 | — † | — | fab | — | https://techcommunity.microsoft.com/blog/azuredevcommunityblog/harness-driven-agents-secure-podcast-pipeline-in-hyperlight-microvm-sandbox/4525512 |
| research | B3 | T3 | — † | — | fab | — | https://upstash.com/blog/software-factory-needs-a-sandbox-per-agent |
| WILD | B2 | U | 2026 | exc | fab | 3.1.8 | https://dev.to/rams901/openai-agents-sdk-sandbox-execution-and-model-native-harness-in-2026-37jn |
| WILD | B2 | U | 2026 | exc | fab | 4.1.1 10.1.9 | https://www.digitalapplied.com/blog/ai-agent-sandboxing-isolation-patterns-2026 |
| WILD | B2 | U | 2026 | url | fab | 3.1.9 | https://emirb.github.io/blog/microvm-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://upstash.com/blog/best-sandbox-providers-for-ai-agents |
| WILD | B2 | U | 2026-05-26 | url | fab | 4.3.1 | https://slavadubrov.github.io/blog/2026/05/26/ai-agent-runtime/ |
| WILD | B2 | U | 2026-04-04 | url | fab | — | https://zylos.ai/research/2026-04-04-ai-agent-sandboxing-security-isolation/ |
| WILD | B2 | U | 2026-02 | exc | fab | 3.3.2 3.4.3 4.1.1 4.1.2 | https://manveerc.substack.com/p/ai-agent-sandboxing-guide |

### 3.1.5

**Q:** Exit test: name a second harness satisfying the same contract; run the same job on both.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-06-18 | exc | fab | — | https://www.openhands.dev/blog/use-any-coding-agent-in-openhands-with-acp |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/hienluu/harness-benchmark |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/polskiTran/HarnessLab |
| research | B1 | T3 | 2026-09 | url | fab | — | https://arxiv.org/abs/2609.04518 |
| research | B1 | T3 | 2026-09-10 | exc | kim gpt | 3.4.5 | https://codex.danielvaughan.com/2026/05/05/agent-skills-open-standard-portable-skills-codex-cli-cross-agent/ |
| research | B1 | T3 | 2026-08 | url | cur | — | https://github.com/AgentWrapper/agent-orchestrator/pull/2412 |
| research | B1 | T3 | 2026-08 | url | cur | — | https://github.com/Untrivial-ai/agent-orchestrator/issues/3317 |
| research | B1 | T3 | 2026-07 | url | cur | — | https://github.com/inflexa-ai/inflexa/blob/a354ed1f/cli/src/modules/harness/agent_switch.ts |
| research | B2 | T3 | 2026-06 | url | cur | — | https://github.com/cjhyy/codeshell/blob/main/packages/core/src/protocol/server.identity-scope.test.ts |
| research | B2 | T3 | 2026-05-27 | exc | kim | — | https://arxiv.org/html/2605.27922 |
| research | B3 | T3 | — † | — | fab | — | https://addyosmani.com/blog/agent-harness-engineering/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/webx_2736/a-reproducible-harness-for-comparing-coding-agents-before-you-trust-their-numbers-1ko7 |
| research | B3 | T3 | — † | — | kim | — | https://www.emergentmind.com/topics/harness-bench |
| research | B3 | T3 | — † | — | cur | — | https://github.com/phenomenoner/agent-harness-core/blob/refs/heads/main/docs/agent-harness-topology-contract.md |
| research | B3 | T3 | — † | — | kim | — | https://implexa.ai/blog/use-claude-skills-in-cursor-codex-gemini |
| research | B3 | T3 | — † | — | fab | — | https://www.port.io/blog/agent-harness-vs-platform-harness |
| research | B3 | T3 | — † | — | kim | — | https://robincartier.com/wiki/wiki-concepts/agent-harness-portability/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://ecorpit.com/ai-coding-agent-harness-claude-code-codex-copilot-cli-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://explainx.ai/blog/top-10-open-closed-source-agent-harnesses-2026 |
| WILD | B2 | U | 2026 | exc | fab | 3.1.6 | https://futureagi.com/blog/best-agent-harness/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://nimbalyst.com/blog/best-agent-harness-for-claude-code-and-codex/ |
| WILD | B3 | U | — † | — | fab | — | https://amdatalakehouse.substack.com/p/open-standards-for-agentic-harnesses |
| WILD | B3 | U | — † | — | fab | — | https://codewave.com/insights/the-agent-harness/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/alexmercedcoder/open-standards-for-agentic-harnesses-5824 |
| WILD | B3 | U | — † | — | fab | — | https://dzone.com/articles/ai-agent-harness-lock-in |
| WILD | B3 | U | — † | — | fab | — | https://harnessrouter.ai/blog/agent-harness-layer |

### 3.1.6

**Q:** Selection rule: footprint, MCP support, sandbox friendliness, license.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://docs.mcpruntime.org/agent-adapters/ |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://docs.mcpruntime.org/runtime/ |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://docs.mcpruntime.org/identity-and-authorization/ |
| primary | B1 | T2 | 2026-06-18 | url | gpt | — | https://github.com/rossoctl/serverless-harness/blob/main/docs/specs/2026-06-18-m10-mcp-code-mode-design.md |
| primary | B2 | T2 | 2026-04-15 | exc | gpt | — | https://openai.com/index/the-next-evolution-of-the-agents-sdk/ |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.harness.agentkit.best/how-it-works |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/sandbaseai/sandbase-harness |
| research | B1 | T3 | 2026-09-03 | url | gpt | — | https://openclawdatabase.com/news/videos/2026-09-03-agent-anatomy-harness-mcp-sandbox/ |
| research | B2 | T3 | 2026-06 | age | cur | — | https://clawaws.com/blog/agentcore-harness-explained/ |
| research | B3 | T3 | — † | — | kim | — | https://cc.bruniaux.com/guide/agent-harness-landscape/ |
| research | B3 | T3 | — † | — | kim | — | https://cordum.io/blog/mcp-firewalls-runtime-hardening-openshell-vs-cordum |
| research | B3 | T3 | — † | — | kim | — | https://gudz.ai/posts/hermes-agent-vs-competitors-2026 |
| research | B3 | T3 | — † | — | kim | — | https://kingy.ai/blog/open-source-coding-agents-2026/ |
| research | B3 | T3 | — † | — | kim | — | https://lumiiadvisory.com/insights/ai-coding-agents-compared |
| research | B3 | T3 | — † | — | kim | — | https://www.openhands.dev/blog/is-claude-code-open-source |
| research | B3 | T3 | — † | — | kim | — | https://shipengtao.com/en/agent-sandbox/ |
| WILD | B1 | U | 2026-08-30 | exc | gpt | — | https://github.laiyagushi.com/sandbaseai/sandbase-harness/discussions/116 |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/best-ai-agent-harness-tools-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.firecrawl.dev/blog/best-ai-coding-agents |
| WILD | B2 | U | 2026 | exc | fab | — | https://pinggy.io/blog/best_open_source_cli_coding_agents/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/RyanAlberts/best-of-Agent-Harnesses |
| WILD | B3 | U | — † | — | gpt | — | https://qgithub.com/sandbaseai/sandbase-harness |

### 3.1.7

**Q:** Runaway detection within a job (repeated identical tool calls, no state progress, step ceiling reached under budget): enforced by the harness (3.1) or policy (2.2); what fires — warn, pause, kill?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B2 | T2 | 2026-03-06 | exc | fab | — | https://github.com/NousResearch/hermes-agent/issues/512 |
| primary | B3 | T2 | — † | — | kim | — | https://docs.langchain.com/oss/python/langchain/guardrails |
| primary | B3 | T2 | — † | — | kim | — | https://docs.nvidia.com/nemo/guardrails/integration-with-third-party-libraries/langchain/agent-middleware |
| primary | B3 | T2 | — † | — | fab | — | https://docs.openclaw.ai/tools/loop-detection |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/browserbase/stagehand/pull/1486 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/oracle/langchain-oracle/pull/50 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/nextbridgehq/agent-loop-guard |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.00038 |
| research | B1 | T3 | 2026-07-02 | exc | fab kim | — | https://arxiv.org/html/2607.01641v1 |
| research | B3 | T3 | — † | — | kim | — | https://www.alphaxiv.org/abs/2607.01641 |
| research | B3 | T3 | — † | — | kim | — | https://www.emergentmind.com/topics/ial-scan |
| research | B3 | T3 | — † | — | fab | — | https://optscale.ai/blog/runaway-agents-loops-drift-recursion |
| research | B3 | T3 | — † | — | kim | — | https://shipwithai.io/blog/loop-guardrails-unattended |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/glossary/infinite-loop/ |
| WILD | B3 | U | — † | — | fab | — | https://cloudzy.com/blog/why-ai-agent-loops-fail-in-production/ |
| WILD | B3 | U | — † | — | fab | — | https://docs.promptise.com/blog/ai-agent-stuck-repeating-tool-call/ |
| WILD | B3 | U | — † | — | fab | — | https://matrixtrak.com/blog/agents-loop-forever-how-to-stop |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@Modexa/the-agent-loop-problem-when-smart-wont-stop-ccbf8489180f |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@Quaxel/stop-runaway-tool-loops-0190218f4c0e |
| WILD | B3 | U | — † | — | fab | — | https://particula.tech/blog/stop-ai-agents-looping-same-tool-call-no-progress |
| WILD | B3 | U | — † | — | fab | — | https://stevekinney.com/writing/agent-loops |

### 3.1.8

**Q:** Agent definition: one declarative, versioned, schema-validated manifest that names the harness class (3.1), orchestration pattern (2.3), sandbox profile (4.1), tool allowlist (3.5) and budget strategy (2.2, 10.4) — or SDK code a developer writes? (Candidates: OASF, a CRD-style spec, framework config.)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://buf.build/agntcy/oasf/file/046ed24ce65a48c1b3bacab657eb151d%3Aagntcy/oasf/types/v1/record.proto |
| core | B3 | T1 | — † | — | fab kim | — | https://docs.agntcy.org/oasf/open-agentic-schema-framework/ |
| core | B3 | T1 | — † | — | kim | — | https://docs.agntcy.org/oasf/agent-record-guide/ |
| core | B3 | T1 | — † | — | fab | — | https://github.com/agntcy/oasf |
| core | B3 | T1 | — † | — | kim | — | https://github.com/agntcy/oasf/blob/main/README.md |
| core | B3 | T1 | — † | — | fab | — | https://schema.oasf.agntcy.org/ |
| primary | B3 | T2 | — † | — | fab kim | 4.1.2 | https://agent-sandbox.sigs.k8s.io/docs/getting_started/overview/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.30546 |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.18787 |
| research | B3 | T3 | — † | — | fab kim | 4.1.2 | https://infragap.com/kubernetes-agent-sandbox/ |
| WILD | B2 | U | 2026-04-17 | url | fab | — | https://codex.danielvaughan.com/2026/04/17/agents-sdk-harness-portable-sandbox-manifests-codex-cli/ |
| WILD | B3 | U | — † | — | fab | — | https://agentswelcome.dev/protocols/oasf |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/mouserider/agentmanifest-a-declarative-spec-where-the-harness-is-the-first-class-decision-lnc |
| WILD | B3 | U | — † | — | fab | — | https://www.emergentmind.com/topics/open-agentic-schema-framework-oasf |

### 3.1.9

**Q:** Local development parity: does the local loop run the same OCI image (4.1) as production (e.g. dev containers), or a lighter substitute; what exactly is guaranteed to match?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | gpt | — | https://containers.dev/overview.html |
| core | B3 | T1 | — † | — | kim | — | https://docs.docker.com/build/building/multi-stage/ |
| core | B3 | T1 | — † | — | gpt | — | https://oci-playground.github.io/specs-latest/specs/image/v1.0.0/oci-image-spec.html |
| core | B3 | T1 | — † | — | gpt | — | https://oci-playground.github.io/specs-latest/specs/image/v1.1.0-rc1/oci-image-spec.html |
| core | B3 | T1 | — † | — | gpt | — | https://oci-playground.github.io/specs-latest/specs/image/v1.1.0-rc4/oci-image-spec.html |
| primary | B1 | T2 | 2026-09-09 | exc | gpt | — | https://github.com/microsoft/vscode-docs/blob/main/docs/devcontainers/containers.md |
| primary | B2 | T2 | 2026-03-31 | exc | gpt | — | https://docs.oracle.com/en/industries/retail/retail-xstore-cloud/26.0.201.0/xocal/G54247_01.pdf |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.oracle.com/en-us/iaas/Content/data-science/using/mod-dep-byoc.htm |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.public.content.oci.oraclecloud.com/en-us/iaas/data-science/using/mod-dep-byoc.htm |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/agentuity/sandbox-python-3.14/tags |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/phiroict/ms_devops_agent/tags |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/arbll/agent-dev/tags |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/sleepysana/devops-agent-base/tags |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/codeany/sandbox-vsc/tags |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/agentscope/runtime-sandbox-gui/tags |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/igetgames/parity/tags |
| primary | B3 | T2 | — † | — | fab | — | https://hub.docker.com/r/agentscope/runtime-sandbox-filesystem/tags |
| research | B2 | T3 | 2026-03-13 | exc | gpt | — | https://blogs.oracle.com/cloud-infrastructure/oci-container-instances-cross-region-recovery |
| research | B2 | T3 | 2026-02-08 | url | fab | — | https://oneuptime.com/blog/post/2026-02-08-how-to-understand-oci-image-and-runtime-specifications/view |
| research | B2 | T3 | 2026-01-30 | url | fab | — | https://oneuptime.com/blog/post/2026-01-30-production-parity/view |
| research | B3 | T3 | — † | — | kim | — | https://buildsoftwaresystems.com/post/docker-build-target-dev-prod/ |
| research | B3 | T3 | — † | — | kim | — | https://crashoverride.com/resources/knowledge-base/container-management/dev-prod-container-drift |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/szkiba/dev-containers-the-missing-runtime-for-agentic-teams-27md |
| research | B3 | T3 | — † | — | fab | — | https://www.docker.com/blog/demystifying-open-container-initiative-oci-specifications/ |
| research | B3 | T3 | — † | — | kim | — | https://infragap.com/advanced-devcontainers/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://distr.sh/glossary/oci-container-artifact-registry/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://explainx.ai/blog/apple-container-1-linux-containers-macos-26-swift-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.cleanstart.com/guide/oci-image-format |
| WILD | B3 | U | — † | — | gpt | — | https://download.plaud.ai/stephenlclarke/container-compose/blob/main/docs/parity/slice-ledger.md |
| WILD | B3 | U | — † | — | fab | — | https://env.dev/guides/dev-containers |
| WILD | B3 | U | — † | — | kim | — | https://www.local-environment-automation.com/environment-sync-secrets-ci-parity/cicd-pipeline-parity-checks/ |
| WILD | B3 | U | — † | — | kim | — | https://www.local-environment-automation.com/containerized-local-environments-docker-compose-patterns/devcontainer-configuration-standards/ |
| WILD | B3 | U | — † | — | fab | — | https://mighil.com/the-complete-guide-to-local-development-environments |
| WILD | B3 | U | — † | — | fab | — | https://rywalker.com/research/microsandbox |

### 3.1.10

**Q:** Agent output contract: is the agent's structured output declared as a versioned schema (JSON Schema, draft pinned) independent of prompt and model, so callers can validate and generate code against it, with compatibility checked when the definition changes?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | gpt | — | https://github.com/json-schema-org/json-schema-spec/blob/main/specs/output/jsonschema-validation-output-machines.md |
| primary | B2 | T2 | 2026-03-16 | exc | gpt | — | https://llmbase.ai/docs/inference/structured-outputs/ |
| primary | B3 | T2 | 2024-08-06 | exc | cur fab gpt | 3.2.1 3.2.4 9.6 | https://openai.com/index/introducing-structured-outputs-in-the-api/ |
| primary | B3 | T2 | — † | — | fab | — | https://code.claude.com/docs/en/agent-sdk/structured-outputs |
| primary | B3 | T2 | — † | — | gpt | 3.2.4 | https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.langchain.com/oss/python/langchain/structured-output |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/earendil-works/pi/issues/1086 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/badlogic/pi-mono/issues/1086 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Axemere-LLC/gismo-contracts |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agentoffernetwork/schema |
| primary | B3 | T2 | — † | — | gpt | 3.2.4 | https://github.com/openai/openai-node/blob/main/docs/structured-outputs.md |
| primary | B3 | T2 | — † | — | fab | 3.2.4 | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
| research | B1 | T3 | 2026-07-13 | exc | kim | — | https://edilec.com/blog/ai-11013/structured-output-contracts-ai-agents/ |
| research | B1 | T3 | 2026-06-21 | url | kim | 5.1.1 | https://zylos.ai/research/2026-06-21-structured-output-validation-multi-agent-workflows/ |
| research | B2 | T3 | 2026-05-30 | exc | fab kim gpt | 3.2.1 10.6.1 | https://www.requesty.ai/blog/structured-outputs-across-llm-providers-the-compatibility-mess |
| research | B2 | T3 | 2026-05-06 | exc | gpt | — | https://blog.simbastack.com/we-rebuilt-the-structured-output-problem-one-layer-up/ |
| research | B2 | T3 | 2026-04-17 | url | kim | — | https://tianpan.co/blog/2026/04/17/semantic-versioning-ai-agents-api-stability |
| research | B2 | T3 | 2026-03-03 | url | gpt | — | https://www.youngju.dev/blog/llm/2026-03-03-structured-output-json-mode-guide.en |
| research | B3 | T3 | — † | — | fab kim | 3.2.4 | https://www.digitalapplied.com/blog/data-contracts-for-ai-agent-pipelines |
| research | B3 | T3 | — † | — | cur kim | 4.3.6 8.1.7 | https://geodocs.dev/ai-agents/agent-prompt-template-versioning-spec |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/@anindyasinghobi/output-format-enforcement-for-agents-json-schema-or-it-didnt-happen-55e421e31254 |
| research | B3 | T3 | — † | — | kim | — | https://rokoss21.tech/en/posts/ai-artifact-schema-evolution/ |
| WILD | B2 | U | 2026 | exc | fab | 3.2.1 3.2.4 | https://collinwilkins.com/articles/structured-output |
| WILD | B2 | U | 2026 | exc | fab | 3.2.4 | https://devtoollab.com/blog/llm-structured-outputs-guide-2026 |
| WILD | B2 | U | 2026 | exc | fab | 3.2.4 | https://ergini.com/blog/openai-structured-outputs |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/glossary/json-validation-metric/ |
| WILD | B2 | U | 2026 | exc | fab | 10.7.5 | https://qubittool.com/blog/json-schema-validation-guide |
| WILD | B2 | U | 2026-01 | exc | fab | — | https://medium.com/@deolesopan/data-contracts-for-agents-keep-tools-and-schemas-stable-as-systems-evolve-8af6f3e024ba |
| WILD | B3 | U | — † | — | fab | 3.2.4 | https://blckalpaca.at/en/knowledge-base/ai-agents/llm-fundamentals-for-agents/strukturierte-outputs-json-schema |
| WILD | B3 | U | — † | — | fab | 3.2.4 | https://www.digitalapplied.com/blog/llm-structured-output-json-reliability-production |

### 3.2.1

**Q:** Is the port the OpenAI-compatible surface or a gateway-native API? Which features (tool calling, structured output, caching, vision) are normalized vs passed through?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://agentgateway.dev/docs/standalone/latest/documentation/llm/api-types/passthrough/ |
| primary | B1 | T2 | 2026-07 | age | cur | 3.2.3 | https://langwatch.ai/docs/ai-gateway/caching-passthrough |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://developers.openai.com/api/docs/guides/function-calling |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://docs.api7.ai/ai-gateway/endpoints/tool-calling |
| primary | B3 | T2 | — † | — | kim | — | https://docs.api7.ai/ai-gateway/endpoints/provider-passthrough |
| primary | B3 | T2 | — † | — | kim | — | https://docs.api7.ai/ai-gateway/endpoints/overview |
| primary | B3 | T2 | — † | — | kim | — | https://docs.litellm.ai/docs/completion/json_mode |
| primary | B3 | T2 | — † | — | kim | — | https://docs.litellm.ai/docs/pass_through/intro |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.llmgateway.io/learn/structured-outputs |
| primary | B3 | T2 | — † | — | kim | — | https://docs.promptgate.dev/features/tool-calling/ |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/lxbme/llm_gateway |
| primary | B3 | T2 | — † | — | gpt | — | https://help.openai.com/en/articles/8555517-function-calling-in-the-openai-api%23.zst |
| research | B2 | T3 | 2026-05-06 | exc | kim gpt | — | https://www.assemblyai.com/blog/reintroducing-llm-gateway |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.braintrust.dev/articles/best-unified-llm-api-providers-2026 |
| WILD | B2 | U | 2026 | exc | fab | 10.6.4 | https://www.braintrust.dev/articles/best-llm-gateways-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://dev.to/ethan_5383afd058ff/6-ai-gateways-compared-for-2026-routing-governance-caching-and-observability-18a7 |
| WILD | B2 | U | 2026 | exc | fab | 3.2.2 10.6.5 | https://www.flotorch.ai/blogs/llm-gateway-comparison-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/blog/llm-function-calling-2025/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.getmaxim.ai/articles/top-5-open-source-llm-gateways-compared-2026/ |
| WILD | B2 | U | 2026 | exc | fab | 10.3.5 10.6.4 | https://inworld.ai/resources/best-llm-gateways |
| WILD | B2 | U | 2026 | exc | fab | 10.6.3 10.6.5 | https://orq.ai/blog/best-llm-gateways |
| WILD | B2 | U | 2026 | exc | fab | — | https://techjacksolutions.com/ai-tools/llm-gateways/best-llm-gateways-2026/ |
| WILD | B2 | U | 2026 | exc | fab | 3.2.2 10.6.3 | https://techsy.io/en/blog/best-llm-gateway-tools |
| WILD | B2 | U | 2026 | exc | fab | — | https://xalen.io/guides/openai-compatible-api-gateways-2026 |
| WILD | B2 | U | 2026 | exc | fab | 10.4.2 | https://zuplo.com/learning-center/best-api-gateways-ai-llm-workloads-2026 |
| WILD | B2 | U | 2026-05 | exc | fab | — | https://medium.com/@dadfor/the-best-ai-gateway-in-2026-a-practical-comparison-of-openrouter-litellm-portkey-and-openmodel-3d4b08fc71b5 |
| WILD | B3 | U | — † | — | kim | — | https://deepwiki.com/BerriAI/litellm/3.8-pass-through-endpoints |
| WILD | B3 | U | — † | — | fab | — | https://www.onprem.ai/en/knowhow/llm-api-standards/ |
| WILD | B3 | U | — † | — | fab | — | https://rubygems.org/gems/ruby_llm |

### 3.2.2

**Q:** Second gateway named (another OSS gateway, or direct SDK) and tested?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/SolaceLabs/solace-agent-mesh/blob/main/examples/gateways/slack_gateway_example.yaml |
| research | B1 | T3 | 2026-08 | url | cur | — | https://github.com/SolaceLabs/solace-agent-mesh/commit/255c56cd5ca7b963b4708c4942d1e3f33a617241 |
| research | B1 | T3 | 2026-07 | age | cur | — | https://community.solace.com/t/tip-how-to-build-a-custom-entrypoint-in-solace-agent-mesh/4827 |
| research | B1 | T3 | 2026-07 | age | cur | — | https://community.solace.com/t/tip-how-do-entrypoints-also-known-as-gateways-work-in-solace-agent-mesh/4800 |
| research | B2 | T3 | 2026-06 | age | cur | — | https://codelabs.solace.dev/codelabs/solace-agent-mesh/ |
| research | B2 | T3 | 2026-06 | exc | kim | — | https://medium.com/@adnanmasood/portkey-vs-litellm-routing-fallbacks-cost-tracking-and-control-the-llm-gateway-playbook-part-195855dc25c3 |
| research | B3 | T3 | — † | — | kim | — | https://api7.ai/kong-ai-gateway-vs-litellm |
| research | B3 | T3 | — † | — | kim | — | https://www.decryptiondigest.com/blog/llm-api-gateway-comparison-portkey-litellm-kong-cloudflare |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/bifrost-vs-litellm-vs-portkey-llm-gateway-2026.html |
| research | B3 | T3 | — † | — | kim | — | https://markaicode.com/vs/litellm-vs-portkey/ |
| research | B3 | T3 | — † | — | kim | — | https://www.merge.dev/blog/portkey-vs-litellm |
| research | B3 | T3 | — † | — | kim | — | https://www.truefoundry.com/blog/bifrost-vs-portkey |
| WILD | B2 | U | 2026 | exc | fab | — | https://api7.ai/litellm-alternative |
| WILD | B2 | U | 2026 | exc | fab | 10.6.3 | https://contabo.com/blog/best-llm-gateways/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.edenai.co/post/best-alternatives-to-litellm |
| WILD | B2 | U | 2026 | exc | fab | — | https://inworld.ai/resources/best-litellm-alternatives |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.kosmoy.com/resources/blog/litellm-alternatives/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://llmgateway.io/blog/litellm-alternatives |
| WILD | B2 | U | 2026 | exc | fab | — | https://openalternative.co/alternatives/litellm |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.truefoundry.com/blog/best-llm-gateways |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.truefoundry.com/blog/litellm-alternatives |
| WILD | B3 | U | — † | — | kim | — | https://gatewayscore.com/compare/litellm-vs-bifrost/ |

### 3.2.3

**Q:** Provider-specific prompt caching: allowed leak or abstracted away?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B2 | T2 | 2026-06-04 | exc | kim | — | https://github.com/envoyproxy/ai-gateway/pull/2193 |
| primary | B3 | T2 | — † | — | fab | — | https://docs.helicone.ai/gateway/concepts/prompt-caching |
| primary | B3 | T2 | — † | — | kim | — | https://docs.llmgateway.io/features/caching/provider-cache-control |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Helicone/ai-sdk-provider/issues/23 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/portkey-ai/gateway/issues/1579 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/musistudio/claude-code-router/issues/1655 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mstuart/peek/blob/f10d2b15/src/model/normalize.ts |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/langchain-ai/langchain/pull/39913 |
| primary | B3 | T2 | — † | — | fab | — | https://openrouter.ai/docs/guides/best-practices/prompt-caching |
| primary | B3 | T2 | — † | — | fab kim | 4.4.4 | https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
| primary | B3 | T2 | — † | — | fab | — | https://vercel.com/docs/ai-gateway/models-and-providers/automatic-caching |
| research | B1 | T3 | 2026-08 | url | cur | — | https://github.com/NousResearch/hermes-agent/pull/79621 |
| research | B1 | T3 | 2026-08 | url | cur | — | https://github.com/NousResearch/hermes-agent/issues/79602 |
| research | B2 | T3 | 2026-06 | age | cur | — | https://www.langchain.com/blog/deep-agents-prompt-caching |
| research | B2 | T3 | 2026-05 | url | cur | — | https://arxiv.org/html/2605.30613v1 |
| research | B3 | T3 | 2025 | url | fab | 4.4.4 | https://introl.com/blog/prompt-caching-infrastructure-llm-cost-latency-reduction-guide-2025 |
| research | B3 | T3 | — † | — | fab | — | https://www.truefoundry.com/blog/provider-agnostic-prompt-caching-llm-gateway |
| WILD | B2 | U | 2026 | exc | fab | — | https://devtoollab.com/blog/prompt-caching-guide |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.digitalapplied.com/blog/prompt-caching-2026-cut-llm-costs-engineering-guide |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/blog/understanding-prompt-caching-for-faster-ai-responses/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.respan.ai/articles/llm-prompt-caching |
| WILD | B2 | U | 2026 | exc | fab | — | https://technspire.com/en/blog/prompt-caching-2026-real-cost-wins |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.techplained.com/llm-prompt-caching |

### 3.2.4

**Q:** Which JSON Schema dialect (and provider strict-mode subset) is the contract for tool input schemas (3.5) and structured model outputs: one shared validator, or per-surface schemas that can drift?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | exc | kim | — | https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2106 |
| core | B3 | T1 | — † | — | kim | — | https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1613 |
| core | B3 | T1 | — † | — | gpt | — | https://json-schema.org/understanding-json-schema/reference/schema |
| core | B3 | T1 | — † | — | kim | — | https://mcp-staging.mintlify.app/seps/2106-json-schema-2020-12 |
| primary | B2 | T2 | 2026-02-04 | exc | gpt | — | https://aws.amazon.com/about-aws/whats-new/2026/02/structured-outputs-available-amazon-bedrock/ |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.aws.amazon.com/en_en/bedrock/latest/userguide/structured-output.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/structured-outputs |
| primary | B3 | T2 | — † | — | fab | — | https://docs.x.ai/developers/model-capabilities/text/structured-outputs |
| primary | B3 | T2 | — † | — | fab | — | https://openrouter.ai/docs/guides/features/structured-outputs |
| primary | B3 | T2 | — † | — | gpt | — | https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use |
| primary | B3 | T2 | — † | — | kim | — | https://ts.sdk.modelcontextprotocol.io/v2/advanced/schema-libraries.html |
| research | B1 | T3 | 2026-08-30 | exc | gpt | — | https://projectcozy.me/blog/json-schema-for-tool-calls |
| research | B3 | T3 | — † | — | kim | — | https://aaif.io/blog/improving-tool-call-reliability-with-json-schema-2020-12 |
| research | B3 | T3 | — † | — | fab | — | https://dev.classmethod.jp/en/articles/amazon-bedrock-structured-outputs-json/ |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/mcp-tool-schemas-json-schema-2020-12.html |
| research | B3 | T3 | — † | — | kim | — | https://specmatic.io/updates/exposed-mcp-servers-are-lying-about-their-schemas/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://devtk.ai/en/blog/ai-structured-output-guide-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.respan.ai/articles/openai-structured-outputs-vs-json-mode |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/openai-structured-outputs-complete-guide |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/slegarraga/tool-schema/blob/main/README.md |

### 3.2.5

**Q:** Provider rate limits and outages: how are 429 / Retry-After signals handled at the gateway (3.2), and what is the degraded-mode commitment — queue, reroute to another provider or model, or fail the job?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.litellm.ai/docs/proxy/reliability |
| primary | B3 | T2 | — † | — | fab | — | https://docs.orq.ai/docs/ai-studio/ai-gateway/retries-and-fallbacks |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kubernetes-sigs/gateway-api-inference-extension/blob/v1.5.0/site-src/guides/flow-control.md |
| research | B2 | T3 | 2026 | exc | fab | — | https://www.requesty.ai/blog/rate-limits-for-llm-providers-openai-anthropic-and-deepseek |
| research | B3 | T3 | — † | — | kim | — | https://aiworkflowlab.dev/article/llm-rate-limiting-429-retries-2026 |
| research | B3 | T3 | — † | — | kim | — | https://apisrouter.com/llm-fallback-architecture-guide |
| research | B3 | T3 | — † | — | fab | — | https://www.getmaxim.ai/articles/handle-429-errors-in-production-llm-applications/ |
| research | B3 | T3 | — † | — | fab | — | https://www.getmaxim.ai/articles/fixing-claude-rate-limit-exceeded-errors-with-an-ai-gateway/ |
| research | B3 | T3 | — † | — | fab | — | https://www.getmaxim.ai/articles/tackle-llm-rate-limits-and-outages-with-an-ai-gateway/ |
| research | B3 | T3 | — † | — | fab kim | 10.3.1 | https://llmgateway.io/blog/how-we-handle-llm-provider-failover |
| research | B3 | T3 | — † | — | fab | — | https://www.parasail.io/blog/multi-region-llm-deployment-gateway-architecture |
| research | B3 | T3 | — † | — | kim | — | https://polystreak.com/blog/llm-gateway-architecture |
| research | B3 | T3 | — † | — | fab | — | https://www.requesty.ai/blog/openrouter-rate-limits-why-they-happen-and-how-multi-provider-fallback-fixes-them |
| research | B3 | T3 | — † | — | fab kim | — | https://www.truefoundry.com/blog/llm-failover-load-balancing-provider-outages |
| WILD | B2 | U | 2026 | exc | fab | — | https://markaicode.com/errors/openrouter-rate-limits-fix/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.respan.ai/articles/openai-api-rate-limits |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/pranay_batta/top-5-enterprise-ai-gateways-for-tackling-rate-limiting-in-llm-apps-1hl6 |
| WILD | B3 | U | — † | — | fab | — | https://evolink.ai/blog/fix-openrouter-429-provider-returned-error |
| WILD | B3 | U | — † | — | fab | — | https://flo2.com/blog/openrouter-rate-limits |
| WILD | B3 | U | — † | — | fab | — | https://lucaberton.com/blog/hermes-agent-troubleshooting/ |
| WILD | B3 | U | — † | — | fab | — | https://mixroute.ai/blog/handle-llm-api-failures/ |

### 3.3.1

**Q:** Image standard OCI; WASM via WASI / component model where used?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07 | age | cur | — | https://wasi.dev/security |
| core | B1 | T1 | 2026-06-11 | exc | fab | — | https://bytecodealliance.org/articles/WASI-0.3 |
| core | B1 | T1 | 2026-06-11 | exc | fab | — | https://github.com/WebAssembly/WASI/releases/tag/v0.3.0 |
| core | B2 | T1 | 2026-06 | age | cur fab kim | 4.1.4 | https://tag-runtime.cncf.io/wgs/wasm/deliverables/wasm-oci-artifact/ |
| core | B3 | T1 | 2025-11 | exc | gpt | — | https://specs.opencontainers.org/image-spec/ |
| core | B3 | T1 | — † | — | fab | 4.1.4 | https://bytecodealliance.org/articles/the-road-to-component-model-1-0 |
| core | B3 | T1 | — † | — | kim | — | https://www.cncf.io/blog/2024/07/09/webassembly-components-the-next-wave-of-cloud-native-computing/ |
| core | B3 | T1 | — † | — | fab | — | https://component-model.bytecodealliance.org/ |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/WebAssembly/WASI/blob/main/specifications/wasi-0.2.12/Overview.md |
| core | B3 | T1 | — † | — | fab | — | https://wasi.dev/releases/wasi-p3 |
| core | B3 | T1 | — † | — | fab | — | https://wasi.dev/roadmap |
| primary | B3 | T2 | 2024-09-25 | exc | cur fab kim | 4.1.4 | https://opensource.microsoft.com/blog/2024/09/25/distributing-webassembly-components-using-oci-registries/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/solo-io/wasm-image-spec |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/wassette |
| primary | B3 | T2 | — † | — | kim | — | https://opensource.microsoft.com/blog/2025/08/06/introducing-wassette-webassembly-based-tools-for-ai-agents/ |
| primary | B3 | T2 | — † | — | cur fab | 4.1.4 | https://wasmcloud.com/docs/overview/packaging/ |
| primary | B3 | T2 | — † | — | fab | 4.1.4 | https://wasmcloud.com/docs/v1/concepts/packaging/ |
| primary | B3 | T2 | — † | — | kim | — | https://wasmedge.org/docs/develop/deploy/intro/ |
| research | B2 | T3 | 2026-06 | age | cur | — | https://component-model.bytecodealliance.org/composing-and-distributing/composing.html |
| research | B2 | T3 | 2026-05 | age | cur | — | https://www.systemshardening.com/articles/wasm/wasm-component-model-security/ |
| research | B2 | T3 | 2026-04-23 | url | kim | — | https://actcore.dev/blog/2026-04-23-introducing-act/ |
| research | B3 | T3 | — † | — | kim | — | https://umatechnology.org/can-wasm-replace-containers/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://dev.to/mysterious_xuanwu_5a00815/webassembly-in-2026-beyond-the-browser-and-into-the-cloud-2599 |
| WILD | B2 | U | 2026 | exc | fab | — | https://medium.com/@jsmanifest/webassembly-component-model-and-wasi-0-3-in-2026-what-javascript-developers-actually-need-to-know-406c8d1ce59c |
| WILD | B2 | U | 2026-04 | url | fab | — | https://www.javacodegeeks.com/2026/04/webassembly-in-2026-where-it-has-landed-what-wasi-0-2-changes-and-why-java-and-kotlin-developers-should-pay-attention-now.html |
| WILD | B3 | U | 2025-02-16 | url | fab | 4.1.4 | https://eunomia.dev/blog/2025/02/16/wasi-and-the-webassembly-component-model-current-status/ |
| WILD | B3 | U | — † | — | fab | — | https://jsmanifest.com/wasm-component-model-wasi-javascript-developers |

### 3.3.2

**Q:** Isolation technology: gVisor, Kata/Firecracker, WASM — selection criteria.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-09-04 | exc | gpt | — | https://agent-sandbox.sigs.k8s.io/docs/use-cases/kata-containers-isolation/ |
| primary | B3 | T2 | — † | — | fab gpt | 3.3.5 | https://github.com/copyleftdev/micro-containers |
| primary | B3 | T2 | — † | — | gpt | 3.3.5 | https://github.com/kata-containers/documentation/blob/master/design/virtualization.md |
| research | B1 | T3 | 2026-08 | age | cur | — | https://www.softwareseni.com/ai-agent-sandboxing-explained-why-docker-is-not-enough-and-what-actually-works/ |
| research | B1 | T3 | 2026-07 | age | cur kim | 4.1.1 cursor:3.3.5 | https://www.augmentcode.com/guides/agent-execution-sandbox |
| research | B1 | T3 | 2026-07-06 | exc | gpt | 3.3.5 | https://www.pandastack.ai/blog/firecracker-vs-kata-vs-gvisor/ |
| research | B1 | T3 | 2026-06-11 | exc | fab gpt | 3.3.5 | https://rywalker.com/research/container-vm-runtimes |
| research | B2 | T3 | 2026-06 | age | cur | — | https://www.golinuxcloud.com/kubernetes-runtimeclass-gvisor/ |
| research | B2 | T3 | 2026-05-16 | url | gpt | — | https://www.youngju.dev/blog/culture/2026-05-16-container-runtimes-containerd-runc-podman-cri-o-kata-gvisor-firecracker-wasm-2026-deep-dive.en |
| research | B2 | T3 | 2026-01-30 | exc | fab gpt | 3.3.5 | https://edera.dev/stories/kata-vs-firecracker-vs-gvisor-isolation-compared |
| research | B3 | T3 | — † | — | cur | cursor:U.11 | https://agentpatterns.ai/security/sandbox-runtime-comparison/ |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/firecracker-vs-gvisor-vs-kata-agent-sandbox-isolation.html |
| research | B3 | T3 | — † | — | kim | — | https://fly.io/learn/firecracker-vs-gvisor/ |
| research | B3 | T3 | — † | — | fab kim | 3.3.5 | https://northflank.com/blog/kata-containers-vs-firecracker-vs-gvisor |
| research | B3 | T3 | — † | — | kim | — | https://www.paperclipped.de/en/blog/ai-agent-sandboxing-code-execution/ |
| research | B3 | T3 | — † | — | kim | — | https://safeguard.sh/resources/blog/gvisor-vs-firecracker-2026 |
| research | B3 | T3 | — † | — | kim | — | https://sandboxreview.com/posts/sandbox-selection-criteria-for-agentic-workloads |
| research | B3 | T3 | — † | — | fab kim | 3.3.5 10.1.9 | https://turion.ai/blog/agent-sandboxing-firecracker-gvisor-microvm-architecture/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://fast.io/resources/best-code-execution-sandboxes-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://menuagentic.com/blogs/gvisor-vs-firecracker-vs-kata-vs-wasm/ |
| WILD | B3 | U | — † | — | fab | — | https://opencomputer.dev/guides/firecracker-vs-cloud-hypervisor-vs-kata/ |
| WILD | B3 | U | — † | — | fab | — | https://www.salmanq.com/blog/understanding-sandboxes/ |

### 3.3.3

**Q:** Network policy as Kubernetes NetworkPolicy / Cilium policy or other; default deny? Does the egress allowlist cover DNS and non-IP channels, or only L3/L4?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-08 | url | cur kim | — | https://github.com/kubernetes-sigs/agent-sandbox/pull/967 |
| core | B2 | T1 | 2026-06 | age | cur gpt | — | https://docs.cilium.io/en/stable/security/policy/deny/ |
| core | B2 | T1 | 2026-06 | age | cur | — | https://docs.cilium.io/en/stable/security/policy/intro/ |
| core | B3 | T1 | 2025-11-06 | url | fab | — | https://www.cncf.io/blog/2025/11/06/safely-managing-cilium-network-policies-in-kubernetes-testing-and-simulation-techniques/ |
| core | B3 | T1 | — † | — | kim | — | https://agent-sandbox.sigs.k8s.io/docs/use-cases/examples/demo-cilium-egress/ |
| core | B3 | T1 | — † | — | kim | — | https://docs.cilium.io/en/latest/security/dns/ |
| primary | B1 | T2 | 2026-07 | url | cur | — | https://github.com/kubernetes-sigs/agent-sandbox/blob/main/examples/policy/network-policy-management/README.md |
| primary | B1 | T2 | 2026-07 | url | cur | — | https://github.com/awslabs/ai-on-eks/blob/main/blueprints/agent-sandbox/egress/manifests/cilium/ciliumnetworkpolicy-sandbox-llm.yaml |
| primary | B3 | T2 | — † | — | fab gpt | — | https://docs.cilium.io/en/latest/security/policy/intro/ |
| primary | B3 | T2 | — † | — | fab gpt | — | https://docs.cilium.io/en/latest/network/servicemesh/default-deny-ingress-policy/ |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.cilium.io/en/stable/security/policy/layer3/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.coreweave.com/products/networking/cilium-network-policy-cks-patterns |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/pnnl/agent-cage/blob/develop/docs/security-model.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/cilium/cilium/blob/main/pkg/k8s/apis/cilium.io/client/crds/v2/ciliumnetworkpolicies.yaml |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/cilium/cilium/blob/main/Documentation/security/policy/layer3.rst?plain=1 |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/cilium/networkpolicy/blob/main/egress-fqdn.yaml |
| research | B2 | T3 | 2026-03-14 | url | fab | — | https://oneuptime.com/blog/post/2026-03-14-how-to-configure-cilium-default-deny-ingress-policy/view |
| research | B2 | T3 | 2026-03-14 | url | fab | — | https://oneuptime.com/blog/post/2026-03-14-how-to-configure-cilium-external-lock-down-policy/view |
| research | B2 | T3 | 2026-03-14 | url | fab | — | https://oneuptime.com/blog/post/2026-03-14-how-to-troubleshoot-cilium-default-deny-ingress-policy/view |
| research | B2 | T3 | 2026-03-13 | url | fab | — | https://oneuptime.com/blog/post/2026-03-13-build-dns-based-egress-policies-cilium/view |
| research | B2 | T3 | 2026-03-13 | url | fab | — | https://oneuptime.com/blog/post/2026-03-13-debug-cilium-policy-does-not-allow-egress/view |
| research | B2 | T3 | 2026-03-03 | url | fab | — | https://oneuptime.com/blog/post/2026-03-03-use-cilium-network-policies-on-talos-linux/view |
| research | B2 | T3 | 2026-01-27 | url | fab | — | https://oneuptime.com/blog/post/2026-01-27-cilium-network-policies/view |
| research | B3 | T3 | — † | — | kim | — | https://blogs.novita.ai/dns-exfiltration-risks-ai-agent-sandboxes/ |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/how-to-lock-down-agent-egress-deny-by-default-network-policy.html |
| research | B3 | T3 | — † | — | kim | — | https://gethasp.com/guides/egress-allowlist-for-coding-agents/ |
| research | B3 | T3 | — † | — | kim | — | https://northflank.com/blog/how-to-design-networking-for-secure-ai-agent-sandboxes |
| WILD | B3 | U | 2024 | url | fab | — | https://advisories.gitlab.com/pkg/golang/github.com/cilium/cilium/CVE-2024-47825/ |
| WILD | B3 | U | — † | — | fab | — | https://imroc.cc/tke/en/networking/cilium/networkpolicy |
| WILD | B3 | U | — † | — | fab | — | https://veducate.co.uk/cilium-network-policies-from-first-principles-to-production/ |

### 3.3.4

**Q:** Provisioning port: create / attach / exec / destroy, independent of the orchestrator (2.4)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur fab kim | 3.5.4 7.2.2 | https://developers.openai.com/api/docs/guides/agents/sandboxes |
| primary | B1 | T2 | 2026-08 | age | cur | — | https://open-sandbox.ai/architecture/ |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://docs.agents-sandbox.com/sandbox_container_lifecycle |
| primary | B3 | T2 | — † | — | fab | — | https://agent-sandbox.github.io/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.e2b.dev/sdk-reference/python-sdk/v2.34.0/sandbox_sync |
| primary | B3 | T2 | — † | — | kim | — | https://docs.e2b.dev/commands/background |
| primary | B3 | T2 | — † | — | kim | — | https://docs.porter.run/sandbox/sdk/typescript/reference |
| primary | B3 | T2 | — † | — | kim | — | https://www.e2b.dev/docs/sandbox |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/synacktraa/sandboxjs |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/arcboxlabs/arcbox/blob/ddf66b8b7b095c4b7127e2437d1278c69bbb82be/docs/sandbox-api.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/koyeb/koyeb-sandbox-sdk-js |
| primary | B3 | T2 | — † | — | fab | — | https://pypi.org/project/agent-sandbox/ |
| primary | B3 | T2 | — † | — | fab | — | https://sandbox-sdk.sh/ |
| primary | B3 | T2 | — † | — | fab | — | https://sandboxagent.dev/ |
| primary | B3 | T2 | — † | — | kim | — | https://vercel.com/docs/sandbox/sdk-reference |
| research | B1 | T3 | 2026-07 | age | cur | — | https://temporal.io/blog/temporal-sandbox-orchestration-harness-the-missing-layer-for-running-agents |
| research | B2 | T3 | 2026 | exc | fab | — | https://northflank.com/blog/daytona-vs-e2b-ai-code-execution-sandboxes |
| research | B2 | T3 | 2026 | exc | fab | 4.1.1 | https://www.spheron.network/blog/ai-agent-code-execution-sandbox-e2b-daytona-firecracker/ |
| research | B2 | T3 | 2026-06 | age | cur | — | https://northflank.com/blog/ai-agent-code-execution-infrastructure |
| research | B3 | T3 | — † | — | fab | — | https://www.bunnyshell.com/guides/coding-agent-sandbox/ |
| research | B3 | T3 | — † | — | fab | — | https://www.bunnyshell.com/guides/sandboxed-environments-ai-coding/ |
| research | B3 | T3 | — † | — | fab | — | https://www.qovery.com/blog/claude-code-sandbox-guide |
| research | B3 | T3 | — † | — | fab | — | https://www.zenml.io/blog/e2b-vs-daytona |
| WILD | B3 | U | — † | — | kim | — | https://deepwiki.com/mattpocock/sandcastle/5.1-sandboxprovider-abstraction |
| WILD | B3 | U | — † | — | fab | — | https://npmx.dev/package/agentbox-sdk |
| WILD | B3 | U | — † | — | fab | — | https://rywalker.com/research/ai-agent-sandboxes |
| WILD | B3 | U | — † | — | fab | — | https://srekubecraft.io/posts/agent-sandbox/ |

### 3.3.5

**Q:** Isolation exit test: has a known container / VM / WASM breakout technique for the chosen tier (3.3.2) been run against it; what is detected or blocked?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://www.cve.org/CVERecord?id=CVE-2024-21626 |
| primary | B2 | T2 | 2026 | url | fab | — | https://aws.amazon.com/security/security-bulletins/2026-015-aws |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/icml-2026-34047/SANDBOXESCAPEBENCH |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mightysai1997/leaky-vessels-dynamic-detector |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/NitroCao/CVE-2024-21626 |
| research | B2 | T3 | 2026 | url | fab | — | https://www.bugcrowd.com/blog/what-we-know-about-copy-fail-cve-2026-31431/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.08433 |
| research | B2 | T3 | 2026-03-23 | exc | kim | — | https://www.aisi.gov.uk/blog/can-ai-agents-escape-their-sandboxes-a-benchmark-for-safely-measuring-container-breakout-capabilities |
| research | B2 | T3 | 2026-03-01 | exc | kim | — | https://doi.org/10.48550/arxiv.2603.02277 |
| research | B3 | T3 | — † | — | kim | — | https://edera.dev/stories/security-without-sacrifice-edera-performance-benchmarking |
| research | B3 | T3 | — † | — | kim | — | https://labs.snyk.io/resources/cve-2024-21626-runc-process-cwd-container-breakout/ |
| WILD | B1 | U | 2026-07-09 | url | fab | 4.1.3 10.1.9 | https://bex.co/blog/2026/07/09/kata-containers-vs-gvisor-runtimeclass-selection |
| WILD | B2 | U | 2026 | url | fab | — | https://www.alekseialeinikov.com/en/blog/topics/devops/microvms-firecracker-vs-gvisor-secure-workloads-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.appsecengineer.com/blog/defending-kubernetes-clusters-against-container-escape-attacks |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/copyleftdev/the-container-runtime-nobody-told-you-about-and-four-others-25e1 |
| WILD | B3 | U | — † | — | fab | — | https://maxprotect.io/blogs/container-escape-cloud-native-security-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://safeguard.sh/resources/blog/container-runtime-comparison-security |
| WILD | B3 | U | — † | — | fab | 10.1.9 | https://sailor.sh/blog/cks-container-sandboxing-gvisor-kata-runtimeclass/ |
| WILD | B3 | U | — † | — | fab | — | https://www.softwareseni.com/firecracker-gvisor-containers-and-webassembly-comparing-isolation-technologies-for-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://www.systemshardening.com/articles/cross-cutting/gvisor-kata-shared-kernel-defense/ |

### 3.4.1

**Q:** What is a workspace: files, memory, shared state — one abstraction or three?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur kim | 4.4.3 | https://java.agentscope.io/v2/en/docs/harness/workspace.html |
| primary | B1 | T2 | 2026-08 | age | cur | — | https://java.agentscope.io/v2/en/docs/harness/filesystem.html |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://java.agentscope.io/v2/en/docs/harness/sandbox.html |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://java.agentscope.io/ |
| primary | B2 | T2 | 2026-03 | exc | fab | — | https://github.com/agentscope-ai/CoPaw/pull/1661 |
| primary | B3 | T2 | — † | — | fab kim | 4.4.3 | https://blogs.oracle.com/developers/comparing-file-systems-and-databases-for-effective-ai-agent-memory-management |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/AIGNE-io/afs |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/daystar7777/agent-work-mem |
| primary | B3 | T2 | — † | — | cur | — | https://java.agentscope.io/v1/en/docs/harness/sandbox/index.html |
| research | B2 | T3 | 2026 | url | fab | 4.3.5 4.4.3 | https://mem0.ai/blog/state-of-ai-agent-memory-2026 |
| research | B2 | T3 | 2026 | exc | fab | 4.4.3 | https://www.taskade.com/blog/agentic-workspaces |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.30306 |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.20021 |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.09947 |
| research | B3 | T3 | 2025-12 | url | fab | — | https://arxiv.org/pdf/2512.05470 |
| research | B3 | T3 | — † | — | kim | — | https://1password.com/blog/filesystems-for-agent-swarms |
| research | B3 | T3 | — † | — | kim | — | https://aigne-io.github.io/afs-paper/ |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2512.05470 |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/@kvkthecreator/why-every-ai-agent-is-quietly-becoming-a-file-system-1d29d7e178b5 |
| research | B3 | T3 | — † | — | kim | — | https://memm.dev/docs/paper/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.cognee.ai/best-ai-memory-layers-for-ai-agents-in-2026-comparison |
| WILD | B2 | U | 2026 | url | fab | — | https://dev.to/jonathanfarrow/the-10-best-ai-memory-layers-for-agents-in-2026-448e |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.eigent.ai/blog/openai-workspace-agents-chatgpt |
| WILD | B2 | U | 2026 | exc | fab | — | https://fast.io/resources/ai-agent-shared-workspace/ |
| WILD | B2 | U | 2026 | exc | fab | 4.4.3 | https://www.make.com/en/blog/agent-workflow-memory |
| WILD | B3 | U | — † | — | kim | — | https://agent-coherence.dev/workspace/ |

### 3.4.2

**Q:** File storage port: POSIX mount vs S3-compatible object API — which is the contract?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab kim | — | https://aws.amazon.com/blogs/storage/orchestrating-multi-agent-ai-architectures-with-amazon-s3-files/ |
| primary | B3 | T2 | — † | — | kim | — | https://aws.amazon.com/s3/features/files/ |
| research | B1 | T3 | 2026-08 | age | cur | — | https://docs.100monkeys.ai/docs/architecture/storage-gateway |
| research | B1 | T3 | 2026-07 | age | cur | — | https://www.mesa.dev/features/filesystem |
| research | B1 | T3 | 2026-07-06 | url | kim | — | https://andrewbaker.ninja/2026/07/06/s3-files-aws-finally-solves-the-object-storage-to-file-system-problem/ |
| research | B2 | T3 | 2026-05 | url | kim | — | https://sandbox0.ai/blog/2026-05/sandbox0-volumes-ai-agent-workspaces |
| research | B2 | T3 | 2026-03 | url | cur kim | — | https://sandbox0.ai/blog/2026-03/shared-storage-for-ai-agents |
| research | B3 | T3 | — † | — | kim | — | https://amulet.so/articles/what-is-agent-native-storage |
| research | B3 | T3 | — † | — | fab | — | https://blog.min.io/filesystem-on-object-store-is-a-bad-idea/ |
| research | B3 | T3 | — † | — | kim | — | https://www.freestyle.sh/blog/product/cloud-storage-vs-working-directories-ai-agents |
| research | B3 | T3 | — † | — | kim | — | https://www.freestyle.sh/blog/engineering/agent-filesystems-git |
| research | B3 | T3 | — † | — | cur | — | https://github.com/VikingMew/tarbox |
| research | B3 | T3 | — † | — | cur | — | https://github.com/meteora-pro/lofs |
| research | B3 | T3 | — † | — | fab | — | https://www.lastweekinaws.com/blog/s3-is-not-a-filesystem-but-now-theres-one-in-front-of-it/ |
| research | B3 | T3 | — † | — | fab | — | https://materializedview.io/p/the-quest-for-a-distributed-posix-fs |
| research | B3 | T3 | — † | — | fab kim | — | https://venturebeat.com/data/amazon-s3-files-gives-ai-agents-a-native-file-system-workspace-ending-the |
| WILD | B2 | U | 2026-05-03 | url | fab | — | https://www.cloudmagazin.com/en/2026/05/03/amazon-s3-files-ga-nfs-mount-object-storage-ml-pipelines/ |
| WILD | B3 | U | — † | — | fab | — | https://www.amplifypartners.com/blog-posts/file-systems-for-agents |
| WILD | B3 | U | — † | — | fab | — | https://www.computerweekly.com/news/366545495/CunoFS-brings-Posix-file-access-to-S3-object-storage-capacity |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/aws-builders/amazon-s3-files-the-game-changer-weve-been-waiting-for-2515 |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/aws/lambda-just-got-a-file-system-i-put-ai-agents-on-it-1ej8 |
| WILD | B3 | U | — † | — | fab | — | https://www.experts-exchange.com/articles/40932/Mounting-Object-store-as-a-File-system.html |
| WILD | B3 | U | — † | — | fab | — | https://lushbinary.com/blog/amazon-s3-files-guide-pricing-use-cases-efs-fsx-comparison/ |
| WILD | B3 | U | — † | — | fab | — | https://objectivefs.com/ |
| WILD | B3 | U | — † | — | fab | — | https://www.storj.io/blog/best-mountpoint-for-s3-alternative |

### 3.4.3

**Q:** Scoping: per job, per session, per tenant; lifecycle and retention.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07 | exc | kim | — | https://www.ietf.org/archive/id/draft-infantado-agent-memory-architecture-00.html |
| primary | B1 | T2 | 2026-08 | age | cur | — | https://docs.kindo.ai/best-practices/memory-and-persistence/ |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://docs.agentarea.ai/agentic-networks |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://docs.atomicstrata.ai/platform/scope |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://docs.amigo.ai/data/workspaces |
| primary | B2 | T2 | 2026-06 | url | cur | — | https://github.com/agentscope-ai/agentscope/blob/3a4e2ae3/src/agentscope/app/workspace_manager/_base.py |
| primary | B2 | T2 | 2026-05 | url | fab | — | https://techcommunity.microsoft.com/blog/agent-365-blog/what%E2%80%99s-new-in-agent-365-may-2026/4516340 |
| primary | B3 | T2 | — † | — | kim | 4.4.5 | https://aws.amazon.com/blogs/machine-learning/designing-lifecycle-policies-for-agentcore-memory/ |
| primary | B3 | T2 | — † | — | fab | — | https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/sessions/overview?authuser=6 |
| primary | B3 | T2 | — † | — | fab | — | https://developers.cloudflare.com/sandbox/concepts/sandboxes |
| primary | B3 | T2 | — † | — | fab | — | https://docs.agentscope.io/versions/2.0.4/en/deploy/agent-service |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/fr_fr/bedrock-agentcore/latest/devguide/runtime-persistent-filesystems.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-lifecycle-settings.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/agentic-ai-multitenant/agentic-ai-multitenant.pdf |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/agentscope-ai/agentscope-java/blob/main/docs/v2/en/docs/harness/workspace.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/redis/agent-memory-server/blob/main/docs/memory-lifecycle.md |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/windows-365/agents/agent-session-lifecycle |
| research | B1 | T3 | 2026-09-05 | url | kim | — | https://explore.n1n.ai/blog/designing-memory-lifecycle-policies-for-long-running-ai-agents-2026-09-05 |
| research | B2 | T3 | 2026-05-30 | url | fab | — | https://gziolo.pl/2026/05/30/research-workspace-boundary-agent-memory/ |
| research | B3 | T3 | — † | — | fab | — | https://aws.amazon.com/cn/blogs/china/agentic-ai-sandbox-practice |
| research | B3 | T3 | — † | — | fab kim | 7.2.2 | https://blaxel.ai/blog/multi-tenant-isolation-ai-agents |
| research | B3 | T3 | — † | — | fab | — | https://blogs.oracle.com/developers/from-prompt-to-persistence-part-1-designing-multi-tenant-agent-memory-schemas-for-saas |
| WILD | B3 | U | — † | — | fab | — | https://www.incubane.com/insights/workday-agent-system-of-record-explained |
| WILD | B3 | U | — † | — | fab | 4.1.1 | https://rywalker.com/research/local-agent-sandboxes |

### 3.4.4

**Q:** Shared-state concurrency: locking, CRDT, last-write-wins?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://crdt.tech/glossary |
| primary | B3 | T2 | — † | — | kim | — | https://agents.open-source.onhelix.ai/reference/store-postgres |
| primary | B3 | T2 | — † | — | cur | — | https://doc.akka.io/japi/akka-core/2.10/akka/cluster/ddata/LWWRegister.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/car-state/latest/car_state/crdt/index.html |
| research | B1 | T3 | 2026-09 | exc | kim | — | https://pub.towardsai.net/the-shared-state-problem-when-two-agents-write-the-same-memory-6854d4ea1ed3 |
| research | B1 | T3 | 2026-08 | url | fab | — | https://arxiv.org/abs/2608.23740 |
| research | B1 | T3 | 2026-08 | exc | kim | — | https://arxiv.org/pdf/2608.23740 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.15376 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.15376 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/abs/2606.15376 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.17076 |
| research | B2 | T3 | 2026-04-16 | url | cur kim | — | https://tianpan.co/blog/2026/04/16/multi-user-shared-agent-state |
| research | B2 | T3 | 2026-04-16 | url | cur | — | https://tianpan.co/blog/2026-04-16-multi-user-shared-agent-state |
| research | B2 | T3 | 2026-03-30 | url | fab | — | https://christophermeiklejohn.com/ai/agents/distributed/zabriskie/2026/03/30/multi-agent-systems-have-a-distributed-systems-problem.html |
| research | B3 | T3 | 2025-10 | url | fab | — | https://arxiv.org/pdf/2510.18893 |
| research | B3 | T3 | 2018-05 | url | fab | — | https://arxiv.org/pdf/1805.06358 |
| research | B3 | T3 | — † | — | kim | — | https://www.alphaxiv.org/abs/2510.18893 |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/pdf/2511.03094 |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/rishi_kora/concurrency-bugs-in-multi-agent-systems-races-deadlocks-idempotency-lan |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.taskade.com/blog/ot-vs-crdt |
| WILD | B2 | U | 2026-03-17 | url | fab | — | https://zylos.ai/research/2026-03-17-crdts-distributed-state-sync-multi-agent-systems/ |
| WILD | B2 | U | 2026-03-09 | url | fab | — | https://zylos.ai/research/2026-03-09-multi-agent-memory-architectures-shared-isolated-hierarchical/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/programmingcentral/scaling-chaos-distributed-context-management-and-agent-state-synchronization-in-multi-agent-systems-5b1 |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/sandeep-alluru/agentcrdt |
| WILD | B3 | U | — † | — | fab | — | https://www.pingcap.com/article/understanding-crdts-and-their-role-in-distributed-systems/ |
| WILD | B3 | U | — † | — | cur | — | https://stackoverflow.com/questions/22339466/how-compare-and-swap-works |
| WILD | B3 | U | — † | — | fab | — | https://thisissiddharthhudda.medium.com/crdts-conflict-free-replicated-data-types-based-agent-memory-8295648ecd7d |

### 3.4.5

**Q:** Skills (bundled instructions plus optional scripts, short of an MCP tool): a first-class, versioned, discoverable artifact in the workspace (3.4), distinct from AGENTS.md (8.1.3) and tools (3.5), or an informal convention?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | 8.1.3 | https://agentskills.io/specification |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agentproto/agentproto/blob/main/specs/aip-3.mdx |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/modelcontextprotocol/registry/discussions/895 |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/microsoft/skills |
| primary | B3 | T2 | — † | — | gpt | — | https://learn.microsoft.com/mt-mt/agent-framework/agents/skills |
| primary | B3 | T2 | — † | — | gpt | — | https://skillmd.com/docs/what-is-an-agent-skill |
| primary | B3 | T2 | — † | — | gpt | — | https://skillmd.com/docs |
| primary | B3 | T2 | — † | — | gpt | — | https://skillmd.com/docs/glossary |
| primary | B3 | T2 | — † | — | gpt | — | https://skillmd.com/ |
| primary | B3 | T2 | — † | — | gpt | — | https://skills.md/docs/agents |
| primary | B3 | T2 | — † | — | gpt | — | https://skills.md/docs/mcp-reference |
| research | B1 | T3 | 2026-09-03 | exc | gpt | — | https://skillmd.com/blog/ai-agent-skills-complete-guide |
| research | B1 | T3 | 2026-09-03 | exc | gpt | — | https://skillmd.com/blog |
| research | B1 | T3 | 2026-07-11 | exc | fab gpt | — | https://devtoollab.com/blog/agent-skills-open-standard-guide |
| research | B3 | T3 | — † | — | gpt | — | https://arthavortex.com/blog/agent-skills-explained-skill-md-vs-mcp |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2604.16911v1 |
| research | B3 | T3 | — † | — | kim | — | https://atlan.com/know/ai-agent/ai-agent-skills/agent-skills-registry/ |
| research | B3 | T3 | — † | — | kim | — | https://geodocs.dev/ai-agents/agent-skill-manifest-specification |
| research | B3 | T3 | — † | — | kim | — | https://localskills.sh/blog/skill-md-vs-claude-md-vs-agents-md |
| research | B3 | T3 | — † | — | kim | — | https://www.skillsboard.sh/agents-md-vs-skill-md |
| research | B3 | T3 | — † | — | kim | — | https://tomevault.io/wtf-is/agents-md-vs-skill-md |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.agensi.io/learn/skill-md-specification-open-standard |
| WILD | B2 | U | 2026 | url | fab | — | https://aiinsightsnews.net/what-are-ai-agent-skills-how-skill-md-works-in-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.articsledge.com/post/agent-skills |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/ai-agent/ai-agent-skills/agent-skills-vs-mcp/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.developersdigest.tech/blog/mcp-servers-vs-agent-skills-2026 |
| WILD | B2 | U | 2026 | exc | fab kim | 8.1.3 8.1.5 | https://www.morphllm.com/agents-md-guide |
| WILD | B2 | U | 2026 | url | fab | — | https://pub.towardsai.net/mcp-vs-agent-skills-what-the-2026-spec-change-finally-settled-for-me-9972d7456fba?gi=76884366df3d |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.webfuse.com/agent-skills-cheat-sheet |
| WILD | B3 | U | — † | — | fab | — | https://blog.logrocket.com/skills-vs-mcp-tools-agent-guide |
| WILD | B3 | U | — † | — | fab | — | https://daily.dev/posts/skills-vs-mcp-tools-for-ai-agents-when-to-use-which-gza3abxxq |
| WILD | B3 | U | — † | — | fab | — | https://deepwiki.com/anthropics/skills/6.1-agent-skills-specification |
| WILD | B3 | U | — † | — | fab | — | https://jannikreinhard.com/agent-skills-vs-mcp/ |

### 3.5.1

**Q:** MCP version; transports allowed (stdio, Streamable HTTP); MCP authorization (OAuth 2.1) required for remote servers?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | exc | cur fab kim gpt | 3.5.7 3.5.10 8.5.2 9.2 cursor:9.4.1 cursor:9.4.2 | https://blog.modelcontextprotocol.io/posts/2026-07-28/ |
| core | B1 | T1 | 2026-07-28 | exc | cur | — | https://github.com/modelcontextprotocol/rust-sdk/blob/main/docs/OAUTH_SUPPORT.md |
| core | B1 | T1 | 2026-07-28 | exc | kim | — | https://modelcontextprotocol.io/specification/draft/basic/authorization |
| core | B3 | T1 | 2025-11-25 | url | gpt | — | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/transports.mdx |
| core | B3 | T1 | 2025-11-25 | url | cur | — | https://modelcontextprotocol.org/specification/2025-11-25/basic/transports |
| core | B3 | T1 | 2025-06-18 | url | gpt | — | https://modelcontextprotocol.io/specification/2025-06-18/basic/transports |
| core | B3 | T1 | 2025-03-26 | url | gpt | — | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-03-26/basic/transports.mdx |
| core | B3 | T1 | 2025-03-26 | url | gpt | — | https://modelcontextprotocol.io/specification/2025-03-26/basic/transports |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://docs.mcp-use.com/python/client/authentication/oauth |
| primary | B1 | T2 | 2026-07-28 | exc | fab | 3.5.10 6.1.3 8.5.2 8.5.6 9.4 | https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/ |
| primary | B1 | T2 | 2026-07-28 | url | fab | — | https://modelcontextprotocol.io/specification/2026-07-28 |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://docs.docker.com/ai/docker-agent/features/remote-mcp/ |
| primary | B3 | T2 | — † | — | fab | 4.3.6 | https://hidekazu-konishi.com/entry/mcp_specification_version_timeline.html |
| primary | B3 | T2 | — † | — | fab | — | https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization |
| research | B1 | T3 | 2026-07-28 | url | fab | — | https://blog.mcpservers.org/posts/mcp-spec-2026-07-28 |
| research | B1 | T3 | 2026-07-23 | exc | fab | — | https://www.theregister.com/devops/2026/07/23/model-context-protocol-prepares-to-break-with-its-stateful-past/5276722 |
| research | B2 | T3 | 2026 | url | fab | — | https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/ |
| research | B2 | T3 | 2026-06 | age | cur | — | https://hidekazu-konishi.com/entry/mcp_server_implementation_reference.html |
| research | B2 | T3 | 2026-01-21 | url | fab | 10.1.2 | https://stackoverflow.blog/2026/01/21/is-that-allowed-authentication-and-authorization-in-model-context-protocol/ |
| research | B3 | T3 | — † | — | fab | — | https://auth0.com/blog/an-introduction-to-mcp-and-authorization/ |
| research | B3 | T3 | — † | — | kim | — | https://www.authgear.com/post/mcp-authentication/ |
| research | B3 | T3 | — † | — | kim | — | https://blog.box.com/securing-your-mcp-servers |
| research | B3 | T3 | — † | — | fab kim | 10.1.2 | https://www.descope.com/blog/post/mcp-auth-spec |
| research | B3 | T3 | — † | — | kim | — | https://mcp.directory/blog/oauth-21-for-remote-mcp-servers-streamable-http-explained-2026 |
| research | B3 | T3 | — † | — | kim | — | https://mcp.mintlify.app/docs/tutorials/security/authorization |
| research | B3 | T3 | — † | — | fab | — | https://mcpcn.com/en/specification/draft/basic/authorization/ |
| research | B3 | T3 | — † | — | fab | — | https://modelcontextprotocol.info/specification/draft/basic/authorization/ |
| research | B3 | T3 | — † | — | fab | — | https://www.permit.io/blog/oauth-on-mcp |
| research | B3 | T3 | — † | — | kim | — | https://ssojet.com/blog/mcp-authentication-oauth-tokens-security-ai-connections |
| research | B3 | T3 | — † | — | kim | — | https://www.wati.io/en/blog/mcp-stdio-vs-streamable-http/ |
| research | B3 | T3 | — † | — | fab kim | 10.1.2 | https://workos.com/blog/what-is-mcp-authorization |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Model_Context_Protocol |
| WILD | B3 | U | — † | — | fab | 10.1.2 | https://maxhammad.substack.com/p/authorization-in-mcp-servers-whats |

### 3.5.2

**Q:** Non-MCP tools (REST/OpenAPI, CLI): wrapped as MCP servers, or a second port?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://microsoft.github.io/mcp-gateway/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Amanbig/mcpify |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/furkan708/mcpify |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/m4cd4r4/mcpwrap |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/harsha-iiiv/openapi-mcp-generator |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/gujord/openapi-mcp |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/evalops/mcp-openapi |
| research | B1 | T3 | 2026-08 | age | cur | — | https://www.solo.io/blog/agentgateway-code-mode-for-openapi-to-mcp |
| research | B1 | T3 | 2026-07 | url | cur | — | https://github.com/kantik001/mcp-gateway |
| research | B1 | T3 | 2026-07 | url | cur | — | https://github.com/BWB03/mcp-gateway |
| research | B1 | T3 | 2026-07-04 | url | fab | — | https://github.com/pvliesdonk/openapi-mcp/blob/main/docs/superpowers/specs/2026-07-04-openapi-generic-wrapper-design.md |
| research | B2 | T3 | 2026 | url | fab | — | https://www.digitalapi.ai/blogs/convert-openapi-specs-into-mcp-server |
| research | B2 | T3 | 2026-06 | url | cur | — | https://github.com/johbau/mcpo |
| research | B3 | T3 | — † | — | fab | — | https://chatforest.com/guides/rest-api-to-mcp-server/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/arobakid/i-tested-7-ways-to-turn-an-openapi-spec-into-an-mcp-server-p5b |
| research | B3 | T3 | — † | — | fab | — | https://gofastmcp.com/integrations/openapi |
| research | B3 | T3 | — † | — | fab | — | https://mcpservers.org/servers/TykTechnologies/api-to-mcp |
| research | B3 | T3 | — † | — | fab | — | https://www.scalekit.com/blog/wrap-mcp-around-existing-api |
| research | B3 | T3 | — † | — | fab | — | https://www.speakeasy.com/mcp/tool-design/generate-mcp-tools-from-openapi/ |
| research | B3 | T3 | — † | — | fab | — | https://www.stainless.com/mcp/from-rest-api-to-mcp-server/ |
| research | B3 | T3 | — † | — | kim | — | https://zuplo.com/blog/mcp-server-generators-compared |

### 3.5.3

**Q:** Per-job tool allowlist decided by policy (2.2); enforced by harness (3.1) or proxy?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://harness.fabric.pro/docs/reference/mcp |
| primary | B1 | T2 | 2026-08 | age | cur | — | https://harness.fabric.pro/docs/reference/policies-approvals |
| primary | B1 | T2 | 2026-07 | age | cur kim | — | https://docs.shield.votal.ai/mcp-runtime-enforcement/ |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://docs.shield.votal.ai/mcp-gateway/ |
| primary | B3 | T2 | — † | — | fab | — | https://developer.harness.io/harness-platform/use-harness-platform/references/allowlist-harness-domains-and-ips |
| primary | B3 | T2 | — † | — | fab | — | https://developer.harness.io/docs/platform/references/allowlist-harness-domains-and-ips/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.openclaw.ai/plugins/sdk-agent-harness |
| primary | B3 | T2 | — † | — | kim | — | https://tyk.io/docs/ai-management/mcp-gateway/policies |
| primary | B3 | T2 | — † | — | kim | — | https://tyk.io/docs/ai-management/mcp-gateway/core-concepts |
| primary | B3 | T2 | — † | — | kim | — | https://tyk.io/docs/nightly/ai-management/mcp-gateway/how-to-mcp-rbac |
| primary | B3 | T2 | — † | — | kim | — | https://tyk.io/docs/ai-management/mcp-gateway/faq |
| research | B2 | T3 | 2026-06 | age | cur | — | https://www.harness.io/blog/identity-and-permissions-for-ai-worker-agents-in-harness |
| research | B2 | T3 | 2026-05 | exc | fab | — | https://arxiv.org/html/2605.18414 |
| research | B3 | T3 | — † | — | fab | — | https://agentpatterns.ai/security/agent-network-egress-policy/ |
| research | B3 | T3 | — † | — | kim | — | https://aisecurity.zone/protocol/hardening-mcp/ |
| research | B3 | T3 | — † | — | fab | — | https://www.beri.net/article/ai-coding-agent-config-allowlist-arbitrary-execution-mcp-unpinned |
| research | B3 | T3 | — † | — | kim | — | https://gethasp.com/guides/self-hosted-mcp-gateway-pattern/ |
| research | B3 | T3 | — † | — | kim | — | https://www.mdpi.com/2079-9292/15/13/2829 |
| WILD | B3 | U | — † | — | fab | — | https://github.com/orgs/community/discussions/169533 |
| WILD | B3 | U | — † | — | fab | — | https://github.com/deepseek-ai/deepseek-harness/discussions/174 |

### 3.5.4

**Q:** Tool execution: same sandbox (3.3) as the agent, or separate?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://openai.github.io/openai-agents-js/guides/sandbox-agents/concepts/ |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://openai.github.io/openai-agents-python/ref/sandbox/sandbox_agent/ |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/agent-governance-toolkit/specs/MCP-SECURITY-GATEWAY-1.0/ |
| primary | B3 | T2 | — † | — | kim | — | https://vercel.com/blog/security-boundaries-in-agentic-architectures |
| research | B2 | T3 | 2026 | url | fab | — | https://blaxel.ai/blog/code-execution-sandboxes-for-ai-agents |
| research | B2 | T3 | 2026 | url | fab | — | https://modal.com/resources/best-code-execution-sandboxes-tool-calling-ai-agents |
| research | B2 | T3 | 2026 | url | fab | — | https://modal.com/resources/best-code-execution-sandboxes-ai-agents |
| research | B2 | T3 | 2026 | url | fab | — | https://northflank.com/blog/how-to-sandbox-ai-agents-in-2026-microVMs-gVisor-isolation-strategies |
| research | B2 | T3 | 2026 | url | fab | — | https://northflank.com/blog/best-code-execution-sandbox-for-ai-agents |
| research | B2 | T3 | 2026-06 | age | cur | — | https://www.mendral.com/blog/agent-harness-belongs-outside-sandbox |
| research | B2 | T3 | 2026-01-10 | url | kim | — | https://appropri8.com/blog/2026/01/10/shipping-mcp-safely-tool-gateway/ |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2602.15945 |
| research | B3 | T3 | — † | — | kim | — | https://blog.sandbase.ai/mcp-execution-boundaries-production-agents/ |
| research | B3 | T3 | — † | — | kim | — | https://gobii.ai/blog/how-we-sandbox-ai-agents-in-production/ |
| research | B3 | T3 | — † | — | cur | — | https://www.infoq.com/vendorcontent/show.action?vcr=054b8afe-244b-4729-a879-0cbe85ff8b05 |
| research | B3 | T3 | — † | — | kim | — | https://predictionguard.com/blog/ai-agent-sandbox-best-practices |

### 3.5.5

**Q:** Result size/time limits and tool telemetry contract.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | url | cur | — | https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/pagination |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/2211 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/anthropics/claude-code/issues/45770 |
| research | B1 | T3 | 2026-08 | age | cur | — | https://www.runpod.io/blog/designing-mcp-tools |
| research | B1 | T3 | 2026-07 | age | cur kim | — | https://www.wati.io/en/blog/mcp-pagination-data-limits/ |
| research | B1 | T3 | 2026-07-02 | url | kim | — | https://zylos.ai/research/2026-07-02-agent-context-transport-envelope-artifact-patterns/ |
| research | B2 | T3 | 2026-06 | age | cur | — | https://connector.zone/guides/pagination-and-large-results/ |
| research | B2 | T3 | 2026-06 | url | cur | — | https://github.com/nyx-builds/mcp-audit |
| research | B2 | T3 | 2026-06-03 | exc | kim | — | https://www.xbstack.com/en/ai/mcp-tool-call-truncated-fix/ |
| research | B3 | T3 | — † | — | fab | — | https://clickhouse.com/resources/engineering/top-opentelemetry-compatible-platforms-2025 |
| research | B3 | T3 | — † | — | fab | — | https://cribl.io/blog/the-telemetry-time-bomb-and-what-to-do-about-it/ |
| research | B3 | T3 | — † | — | fab | — | https://www.dash0.com/comparisons/best-opentelemetry-tools |
| research | B3 | T3 | — † | — | fab | — | https://www.digitalapplied.com/blog/when-a-tool-call-takes-ten-minutes |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/tool-result-too-large-for-context-window.html |
| research | B3 | T3 | — † | — | fab | — | https://www.selector.ai/learning-center/network-telemetry-how-it-works-protocols-and-use-cases/ |
| research | B3 | T3 | — † | — | kim | — | https://signoz.io/blog/mcp-observability-with-otel/ |
| research | B3 | T3 | — † | — | kim | — | https://stackademic.com/blog/reducing-mcp-response-sizes-for-llm-context-limits |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@Quaxel/tool-contracts-12-clauses-that-prevent-silent-misfires-c9e8bbd97b6f |
| WILD | B3 | U | — † | — | fab | — | https://smithery.ai/skills/metabench/telemetry-contracts |

### 3.5.6

**Q:** Tool poisoning / rug-pull: are MCP tool descriptions, schemas, and annotations hashed and pinned at approval time, with re-approval (2.2) required before any change takes effect?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025 | url | fab | — | https://owasp.org/www-project-mcp-top-10/2025/MCP03-2025%E2%80%93Tool-Poisoning |
| core | B3 | T1 | — † | — | fab | — | https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html |
| primary | B1 | T2 | 2026-07-09 | exc | kim | — | https://github.com/vercel/ai/pull/16902 |
| primary | B3 | T2 | — † | — | fab | — | https://ai-sdk.dev/docs/agents/tool-approvals |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-governance-toolkit/blob/main/agent-governance-python/agent-os/src/agent_os/mcp_security.py |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/agent-governance-toolkit/integrations/mcp-trust-guide/ |
| research | B1 | T3 | 2026-07 | exc | kim | — | https://pondero.ai/agents/guides/mcp-tool-poisoning-defense-guide-july-2026/ |
| research | B2 | T3 | 2026 | url | fab | — | https://labs.cloudsecurityalliance.org/research/csa-research-note-mcp-tool-poisoning-ai-agent-exfiltration-2/ |
| research | B2 | T3 | 2026 | url | fab | — | https://www.practical-devsecops.com/mcp-tool-poisoning/ |
| research | B2 | T3 | 2026 | url | fab | — | https://www.speakeasy.com/resources/mcp-tool-poisoning/ |
| research | B2 | T3 | 2026-06-02 | exc | gpt | — | https://agentguardian.io/blogs/mcp-tool-description-rug-pull |
| research | B2 | T3 | 2026-03-05 | exc | gpt | — | https://pipelab.org/blog/tool-poisoning-mcp-attack-surface/ |
| research | B3 | T3 | 2025 | url | fab | — | https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2508.14925 |
| research | B3 | T3 | — † | — | kim | — | https://www.digitalapplied.com/blog/vercel-ai-sdk-mcp-tool-drift-fingerprint-security-2026 |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/how-to-fingerprint-mcp-tools-detect-drift.html |
| research | B3 | T3 | — † | — | kim | — | https://mcp-hangar.io/learn/digest-pinning |
| research | B3 | T3 | — † | — | gpt | — | https://pipelab.org/learn/mcp-tool-poisoning/ |
| research | B3 | T3 | — † | — | kim | — | https://security.unboundcompute.com/mcp-tool-pinning/ |

### 3.5.7

**Q:** Per-call tool credentials: is the credential presented to a tool or MCP server scoped to that invocation (audience, minimal scope, short TTL), or one session credential reused across every call?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | url | gpt | — | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx |
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/html/rfc8693 |
| research | B1 | T3 | 2026-08 | url | fab | — | https://buildwithfern.com/post/api-authentication-integration-tools-oauth-claude |
| research | B1 | T3 | 2026-08 | exc | fab | — | https://techcommunity.microsoft.com/blog/microsoft-security-blog/the-state-of-mcp-security-in-2026/4531327 |
| research | B2 | T3 | 2026 | url | fab | — | https://www.arcade.dev/blog/ai-agent-authentication-authorization/ |
| research | B2 | T3 | 2026 | url | fab kim | — | https://workos.com/blog/ai-agent-auth-checklist |
| research | B3 | T3 | — † | — | fab | — | https://www.descope.com/learn/post/client-credentials-flow |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/mgonzalezo/implementing-rfc-8693-token-exchange-in-agentgateway-a-complete-tutorial-3g3p |
| research | B3 | T3 | — † | — | kim | — | https://guptadeepak.com/guides/identity-for-ai-agents/ |
| research | B3 | T3 | — † | — | fab kim | 10.1.3 | https://mojoauth.com/blog/oauth-2-0-token-exchange-rfc-8693-for-agent-delegation-a-worked-example |
| research | B3 | T3 | — † | — | kim | — | https://praesidia.ai/blog/agent-to-tool-authorization-token-exchange |
| research | B3 | T3 | — † | — | fab | — | https://www.scalekit.com/blog/tool-calling-authentication-ai-agents |
| research | B3 | T3 | — † | — | fab | — | https://securew2.com/blog/oauth-for-ai-agents |
| research | B3 | T3 | — † | — | fab kim | — | https://supertokens.com/blog/auth-for-ai-agents |
| research | B3 | T3 | — † | — | kim | — | https://zuplo.com/learning-center/oauth2-token-exchange-identity-propagation |
| WILD | B3 | U | — † | — | fab | — | https://guptadeepak.com/credential-lifecycle-management-for-ai-agents-from-24-hour-tokens-to-300-second-ephemeral-authentication/ |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/faq/why-do-short-lived-credentials-matter-for-sensitive-internal-applications/ |

### 3.5.8

**Q:** MCP resources and prompts (app- and user-controlled) alongside tools: are MCP resources the retrieval port for knowledge (8.3) and memory (4.4), or is everything exposed as a tool?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-03-26 | url | gpt | — | https://modelcontextprotocol.io/specification/2025-03-26/basic/index |
| core | B3 | T1 | 2025-03-26 | url | gpt | — | https://modelcontextprotocol.io/specification/2025-03-26/index |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-retrieve |
| research | B2 | T3 | 2026 | url | fab | — | https://dev.to/mind_anthony/mcp-memory-server-what-it-is-how-to-choose-2026-3co5 |
| research | B2 | T3 | 2026 | url | fab | — | https://dev.to/aws-heroes/mcp-prompts-and-resources-the-primitives-youre-not-using-3oo1 |
| research | B2 | T3 | 2026 | url | fab | 10.3.2 | https://www.digitalapplied.com/blog/mcp-tool-use-vocabulary-reference-guide-2026 |
| research | B2 | T3 | 2026 | url | fab | — | https://techcommunity.microsoft.com/blog/azuredevcommunityblog/mcp-demystified-tools-vs-resources-vs-prompts-explained-simply/4508057 |
| research | B3 | T3 | — † | — | kim | — | https://dvnc.dev/blog/mcp-resources-vs-tools-production-server |
| research | B3 | T3 | — † | — | kim | — | https://gingerlabs.ai/blog/mcp-tools-resources-prompts |
| research | B3 | T3 | — † | — | kim | — | https://gingerlabs.ai/blog/designing-mcp-servers-autonomous-ai-agents |
| research | B3 | T3 | — † | — | kim | — | https://www.matthewswong.com/en/blog/mcp-tools-resources-prompts-primitives/ |
| research | B3 | T3 | — † | — | kim | — | https://www.mcpforge.tech/blog/when-to-use-mcp-resources |
| research | B3 | T3 | — † | — | kim | — | https://theaugmenteddev.com/blog/mcp-resources-tools-prompts-when-to-use |
| research | B3 | T3 | — † | — | kim | — | https://workos.com/blog/designing-mcp-server-from-rest-api |
| WILD | B3 | U | — † | — | fab | — | https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/knowledge-management--memory.md |
| WILD | B3 | U | — † | — | fab | — | https://github.com/jeanibarz/knowledge-base-mcp-server |
| WILD | B3 | U | — † | — | fab | — | https://github.com/olafgeibig/knowledge-mcp |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/categories/knowledge-and-memory |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/@maxzrff/KnowledgeMCP/blob/9ae6a88091c0358725cb921250ac263f9592a613/COMPLETION_SUMMARY.md |
| WILD | B3 | U | — † | — | fab | — | https://lobehub.com/mcp/yodakeisuke-mcp-memory-domain-knowledge |
| WILD | B3 | U | — † | — | fab | — | https://mcp.so/server/knowledge-base-mcp-server |
| WILD | B3 | U | — † | — | fab | — | https://mcpservers.org/servers/modelcontextprotocol/memory |
| WILD | B3 | U | — † | — | fab | — | https://playbooks.com/mcp/geeksfino-knowledge-base |
| WILD | B3 | U | — † | — | fab | — | https://www.pulsemcp.com/servers/geeksfino-knowledge-base |
| WILD | B3 | U | — † | — | fab | — | https://www.pulsemcp.com/servers/jeanibarz-knowledge-base-retrieval |

### 3.5.9

**Q:** MCP sampling (a server requesting a completion from the client): does it route through the model interface (3.2) and inherit budget and policy checks (2.2), or is it a separate path?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | url | gpt | — | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/client/sampling.mdx |
| core | B1 | T1 | 2026-07-28 | exc | fab kim | — | https://modelcontextprotocol.io/specification/2026-07-28/client/sampling |
| core | B3 | T1 | 2025-11-25 | url | fab gpt | — | https://modelcontextprotocol.io/specification/2025-11-25/client/sampling |
| core | B3 | T1 | — † | — | gpt | — | https://modelcontextprotocol.io/specification/draft/client/sampling |
| primary | B3 | T2 | — † | — | kim | — | https://ai-sdk.dev/providers/community-providers/mcp-sampling |
| primary | B3 | T2 | — † | — | fab | — | https://csharp.sdk.modelcontextprotocol.io/v2/concepts/sampling/sampling.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Kuadrant/mcp-gateway/issues/949 |
| primary | B3 | T2 | — † | — | fab | — | https://mcpcn.com/en/docs/concepts/sampling/ |
| primary | B3 | T2 | — † | — | fab | — | https://modelcontextprotocol.info/docs/concepts/sampling/ |
| research | B2 | T3 | 2026 | url | fab | 8.5.2 10.1.2 | https://workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026 |
| research | B3 | T3 | — † | — | fab | — | https://www.agent-wars.com/news/2026-06-23-mcp-goes-stateless-deprecates-sampling |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2602.14878v1 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2512.08290 |
| research | B3 | T3 | — † | — | kim | — | https://www.arxiv.org/pdf/2601.17549 |
| research | B3 | T3 | — † | — | kim | — | https://byteiota.com/mcp-2026-07-28-what-breaks-and-how-to-migrate/ |
| research | B3 | T3 | — † | — | fab | — | https://www.dailydoseofds.com/model-context-protocol-crash-course-part-5/ |
| research | B3 | T3 | — † | — | kim | — | https://gethasp.com/guides/mcp-sampling-attack-vector/ |
| research | B3 | T3 | — † | — | fab | — | https://imti.co/mcp-sampling/ |
| research | B3 | T3 | — † | — | kim | — | https://jacar.es/en/mcp-specification-2026-07-28/ |
| research | B3 | T3 | — † | — | fab | — | https://mingzilla.github.io/specification/mcp-sampling-guide.html |
| research | B3 | T3 | — † | — | kim | — | https://satgate.io/blog/mcp-gateway-guide |
| research | B3 | T3 | — † | — | fab | — | https://www.speakeasy.com/mcp/core-concepts/sampling/ |
| research | B3 | T3 | — † | — | fab | — | https://www.stainless.com/mcp/sampling/ |
| WILD | B3 | U | 2025-11-25 | url | gpt | — | https://mcp.mintlify.app/specification/2025-11-25/client/sampling |
| WILD | B3 | U | 2025-06-18 | url | gpt | — | https://mcp.mintlify.app/specification/2025-06-18/client/sampling |
| WILD | B3 | U | — † | — | fab | — | https://modelcontextprotocol.info/specification/ |

### 3.5.10

**Q:** MCP elicitation (a tool requesting input mid-call) when the job is headless (1.2, 1.3): deny, block, or route to an operator queue?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | url | gpt | — | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/changelog.mdx |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/crate/mcp2cli/latest/source/docs/features/elicitation-and-sampling.md |
| primary | B3 | T2 | — † | — | kim | — | https://gofastmcp.com/clients/elicitation |
| primary | B3 | T2 | — † | — | kim | — | https://gofastmcp.com/servers/elicitation |
| primary | B3 | T2 | — † | — | fab | — | https://payloadcms.com/docs/jobs-queue/overview |
| primary | B3 | T2 | — † | — | kim | — | https://unpkg.com/agents@0.21.0/docs/mcp-client.md |
| research | B1 | T3 | 2026-08-05 | exc | fab | — | https://equixly.com/blog/2026/08/05/stateless-mcp/ |
| research | B2 | T3 | 2026 | url | fab | — | https://appwrite.io/blog/post/mcp-goes-stateless-in-the-2026-07-28-specification |
| research | B2 | T3 | 2026 | url | fab | — | https://aws.amazon.com/blogs/machine-learning/how-agentcore-gateway-supports-the-mcp-2026-07-28-spec/ |
| research | B2 | T3 | 2026 | url | fab | — | https://www.cdata.com/blog/mcp-2026-07-28-release |
| research | B2 | T3 | 2026 | url | fab | — | https://www.digitalapplied.com/blog/mcp-2026-07-28-stateless-spec-agent-infrastructure-2026 |
| research | B2 | T3 | 2026 | url | cur fab | cursor:9.4.5 | https://www.langchain.com/blog/mcp-in-langchain-stateless-protocol-elicitation-and-more |
| research | B3 | T3 | — † | — | kim | — | https://agenticcontrolplane.com/blog/claude-code-headless-approvals |
| research | B3 | T3 | — † | — | kim | — | https://agentpatterns.ai/tool-engineering/mcp-elicitation/ |
| research | B3 | T3 | — † | — | kim | — | https://claudefa.st/blog/guide/changelog |
| research | B3 | T3 | — † | — | kim | — | https://www.developersdigest.tech/guides/elicitation-hook |
| research | B3 | T3 | — † | — | fab | — | https://hidekazu-konishi.com/entry/claude_code_cicd_and_headless_automation.html |
| research | B3 | T3 | — † | — | fab | — | https://www.inngest.com/uses/serverless-cron-jobs |
| research | B3 | T3 | — † | — | fab | — | https://mise.jdx.dev/tasks/task-configuration.html |
| research | B3 | T3 | — † | — | fab | — | https://usagebar.com/blog/how-to-do-cron-job-setup-on-claude-code |
| WILD | B2 | U | 2026 | url | fab | — | https://shahabas.me/blogs/stateless-mcp-2026-spec-explained.html |
| WILD | B3 | U | — † | — | fab | — | https://www.basedlabs.ai/articles/best-headless-ai-workflow-platforms-in-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.biggestgoal.ai/l/claude-code-headless |
| WILD | B3 | U | — † | — | fab | — | https://www.mindstudio.ai/blog/claude-code-headless-mode-autonomous-agents |

### 3.5.11

**Q:** Do tool definitions ship with their own contract tests (consumer-driven, Pact-style, or other) runnable in isolation from the harness (3.1) and the end-to-end evals (6.2, 7.3)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.pact.io/implementation_guides/javascript/docs/consumer |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mefellows/pact-mcp-plugin/blob/main/docs/usage.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mefellows/pact-mcp-plugin/blob/main/docs/plans/pact-mcp-plugin-implementation-plan.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mefellows/pact-mcp-plugin/blob/main/docs/bdct-walkthrough.md |
| primary | B3 | T2 | — † | — | kim | — | https://www.npmjs.com/package/@pactflow/pact-mcp-plugin |
| primary | B3 | T2 | — † | — | kim | — | https://pypi.org/project/mcp-pact/ |
| research | B2 | T3 | 2026 | url | fab | — | https://ncluster.tech/blog/contract-testing-pact-2026/ |
| research | B2 | T3 | 2026 | url | fab | — | https://qaskills.sh/blog/pact-contract-testing-guide-2026 |
| research | B2 | T3 | 2026 | url | fab | — | https://qaskills.sh/blog/contract-testing-pact-complete-guide |
| research | B2 | T3 | 2026 | url | fab | — | https://qaskills.sh/blog/contract-testing-pact-complete-guide-2026 |
| research | B2 | T3 | 2026 | url | fab | — | https://qaskills.sh/blog/pact-consumer-driven-contract-reference-2026 |
| research | B2 | T3 | 2026 | url | fab | — | https://www.sqaexperts.com/consumerdriven-contract-testing-with-pact-microservices-qa-guide-for-2026 |
| research | B2 | T3 | 2026-01-24 | age | fab | — | https://oneuptime.com/blog/post/2026-01-24-contract-testing-pact/view |
| research | B3 | T3 | — † | — | fab | — | https://jfrog.com/learn/devsecops/contract-testing/ |
| research | B3 | T3 | — † | — | fab | — | https://pflb.us/blog/contract-testing/ |
| research | B3 | T3 | — † | — | fab | — | https://www.testingmind.com/contract-testing-an-introduction-and-guide/ |
| research | B3 | T3 | — † | — | fab | — | https://testrigor.com/blog/api-contract-testing/ |
| research | B3 | T3 | — † | — | fab | — | https://www.tweag.io/blog/2025-01-23-contract-testing/ |
| WILD | B3 | U | — † | — | fab | — | https://www.hypertest.co/contract-testing/best-api-contract-testing-tools |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.USPTO.gov/dirsearch-public/print/downloadPdf/6938186 |
| WILD | B3 | U | — † | — | fab | — | https://www.testsprite.com/use-cases/en/the-best-contract-testing-tools |

## 4. Execution & Runtime

### 4.1.1

**Q:** Profile definition format (versioned); fields: isolation tier, network, mounts, egress allowlist, limits, GPU.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://agent-sandbox.sigs.k8s.io/docs/api/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.cloud.google.com/kubernetes-engine/docs/concepts/machine-learning/agent-sandbox |
| primary | B3 | T2 | — † | — | cur kim | — | https://docs.coreweave.com/products/sandboxes/reference/profile |
| primary | B3 | T2 | — † | — | cur kim | — | https://docs.coreweave.com/products/sandboxes/profiles/profile-examples |
| primary | B3 | T2 | — † | — | cur | — | https://docs.coreweave.com/products/sandboxes/profiles/configure |
| primary | B3 | T2 | — † | — | cur | — | https://docs.coreweave.com/products/sandboxes/reference/control-plane-api |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/styrene-lab/omegon/blob/main/core/crates/omegon/src/nex/profile.rs |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kubernetes-sigs/agent-sandbox/blob/main/extensions/api/v1alpha1/sandboxtemplate_types.go |
| research | B2 | T3 | 2026 | exc | fab | — | https://northflank.com/blog/what-is-a-sandbox-environment |
| research | B3 | T3 | — † | — | fab | — | https://www.aisi.gov.uk/category/engineering |
| research | B3 | T3 | — † | — | fab | — | https://blogs.novita.ai/ai-agent-sandbox-faq/ |
| research | B3 | T3 | — † | — | fab | — | https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke/ |
| research | B3 | T3 | — † | — | kim | — | https://geodocs.dev/ai-agents/agent-sandbox-documentation-spec |
| WILD | B3 | U | — † | — | fab | — | https://github.com/bureado/awesome-agent-runtime-security |
| WILD | B3 | U | — † | — | fab | — | https://www.luiscardoso.dev/blog/sandboxes-for-ai |

### 4.1.2

**Q:** Everything the sandbox (3.3) needs is declared in the profile, not in code?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://agent-sandbox.sigs.k8s.io/docs/use-cases/examples/quickstart/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.daytona.io/docs/en/declarative-builder/ |
| primary | B3 | T2 | — † | — | kim | — | https://e2b.dev/docs/template/quickstart |
| primary | B3 | T2 | — † | — | kim | — | https://e2b.dev/blog/introducing-build-system-2-0 |
| primary | B3 | T2 | — † | — | fab | — | https://github.github.com/gh-aw/reference/sandbox/ |
| research | B2 | T3 | 2026 | exc | fab | — | https://blaxel.ai/blog/codesandbox-alternatives |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.26524 |
| WILD | B2 | U | 2026 | url | fab | 10.1.9 | https://dev.to/aiagentengineering/how-to-sandbox-ai-agents-in-2026-firecracker-gvisor-runtimes-isolation-strategies-14pk |
| WILD | B2 | U | 2026 | url | fab | — | https://www.developersdigest.tech/blog/microsoft-mxc-developer-guide-2026 |
| WILD | B2 | U | 2026 | exc | fab | 10.1.9 | https://thebackenddevelopers.substack.com/p/runtime-verification-for-ai-agents |
| WILD | B2 | U | 2026-05 | exc | fab | — | https://gist.github.com/wincent/2752d8d97727577050c043e4ff9e386e |
| WILD | B3 | U | — † | — | fab | — | https://github.com/restyler/awesome-sandbox |
| WILD | B3 | U | — † | — | fab | — | https://pradiptabanerjee.medium.com/agent-sandbox-on-kubernetes-e7654ab4827a |

### 4.1.3

**Q:** Mapping rule: job class → profile; is it declared in the workflow (2.4) or by policy (2.2)? Who can override?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.gensparx.com/gateway/sandbox-vs-tool-policy-vs-elevated |
| primary | B3 | T2 | — † | — | kim | — | https://docs.okd.io/latest/security/security_profiles_operator/spo-seccomp.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.openclaw.ai/tools/multi-agent-sandbox-tools |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/chimera-kube/pod-runtime-class-policy |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/kubewarden/pod-runtime-class-policy |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/kubernetes/enhancements/tree/master/keps/sig-node/585-runtime-class |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/585-runtime-class/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/openclaw/openclaw/blob/main/docs/tools/multi-agent-sandbox-tools.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kubernetes-sigs/security-profiles-operator/blob/master/installation-usage.md |
| primary | B3 | T2 | — † | — | fab | — | https://kubernetes.io/docs/concepts/containers/runtime-class/ |
| primary | B3 | T2 | — † | — | fab | — | https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/ |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/microsoft-identity-manager/reference/get-workflow-policy |
| research | B3 | T3 | — † | — | kim | — | https://cs.unibg.it/seclab-papers/2025/CLOUDCOM/secure-scheduling.pdf |
| research | B3 | T3 | — † | — | fab | — | https://labs.iximiuz.com/tutorials/kubernetes-runtime-class-61506808 |
| WILD | B2 | U | 2026 | exc | fab | — | https://devsecopsschool.com/blog/seccomp/ |
| WILD | B2 | U | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-runtimeclass-windows-linux-routing/view |
| WILD | B2 | U | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-containerd-runtime-classes-isolation/view |
| WILD | B2 | U | 2026-01-30 | url | fab | 10.1.9 | https://oneuptime.com/blog/post/2026-01-30-kubernetes-runtimeclass/view |
| WILD | B3 | U | — † | — | fab | — | https://docs.informatica.com/data-quality-and-governance/data-quality/10-4-0/developer-workflow-guide/mapping-task/mapping-task-input/override-mapping-parameters-during-a-workflow-run.html |
| WILD | B3 | U | — † | — | fab | — | https://forum.gitlab.com/t/interaction-between-workflow-rules-and-rules/49704 |
| WILD | B3 | U | — † | — | fab | — | https://gitlab.com/gitlab-org/gitlab/-/issues/512123 |
| WILD | B3 | U | — † | — | fab | — | https://help.salesforce.com/s/articleView?id=platform.customize_wf.htm&language=en_US&type=5 |

### 4.1.4

**Q:** OCI / WASI as the only image contracts?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2024-03-13 | url | fab | — | https://opencontainers.org/posts/blog/2024-03-13-image-and-distribution-1-1/ |
| core | B3 | T1 | — † | — | fab | — | https://bytecodealliance.org/articles/WASI-0.2.1 |
| core | B3 | T1 | — † | — | cur | — | https://github.com/opencontainers/image-spec/blob/31de01337887e96f3f25216a9b8d85efa4ba6e83/image-index.md |
| core | B3 | T1 | — † | — | kim | — | https://github.com/opencontainers/distribution-spec/blob/acfc11dad63159052f98dd9afab04adf59e6ed8f/spec.md |
| core | B3 | T1 | — † | — | cur | — | https://oci-playground.github.io/specs-latest/specs/image/v1.1.0-rc3/oci-image-spec.pdf |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/containerd/containerd/issues/10179 |
| primary | B3 | T2 | — † | — | kim | — | https://oras.land/docs/concepts/artifact |
| primary | B3 | T2 | — † | — | fab | — | https://wasmcloud.com/docs/overview/interfaces/ |
| research | B3 | T3 | 2025-12-08 | url | fab | 8.2.1 8.2.2 | https://oneuptime.com/blog/post/2025-12-08-oci-artifacts-explained/view |
| research | B3 | T3 | — † | — | kim | — | https://www.toolsku.com/en/blog/wasm-oci-registry-distribution-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://techbytes.app/posts/wasm-component-model-2026-cloud-interop-deep-dive/ |

### 4.2.1

**Q:** Scheduler port: Kubernetes, Ray, Slurm, bare Docker — which operations are required?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://docs.coreweave.com/products/sunk/tutorials/ray-on-sunk |
| primary | B3 | T2 | — † | — | cur | — | https://docs.ray.io/en/latest/ray-core/internals/port-service-discovery.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.ray.io/en/releases-2.40.0/cluster/vms/user-guides/community/slurm.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.ray.io/en/latest/cluster/vms/user-guides/community/slurm.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/mazrean/dockportless |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/purkka/supernetes |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mrozacki/k8s-bridge/blob/main/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://slinky.schedmd.com/slurm-bridge/v1.2.0/index.html |
| research | B2 | T3 | 2026 | exc | fab | 4.2.3 | https://www.whitefiber.com/blog/slurm-vs-kubernetes |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.12031 |
| research | B3 | T3 | 2024-10 | url | fab | — | https://arxiv.org/pdf/2410.10634 |
| research | B3 | T3 | — † | — | cur | — | https://ai-infrastructure.net/ray-on-slurm/ |
| research | B3 | T3 | — † | — | kim | — | https://ai-infrastructure.net/orchestration-decision-guide/ |
| research | B3 | T3 | — † | — | fab kim | 4.2.3 | https://clear.ml/blog/managing-across-schedulers-hpc-meets-kubernetes |
| research | B3 | T3 | — † | — | kim | — | https://hcompany.ai/unlocking-online-rl-skypilot |
| research | B3 | T3 | — † | — | kim | — | https://kentino.com/pages/job-scheduling-for-ai-clusters-slurm-kubernetes-ray-and-knowing-when-you-need-none-of-them |
| research | B3 | T3 | — † | — | fab | — | https://shakticloud.ai/blog/comparing-kubernetes-vs-slurm-for-ai-workloads-when-to-use-what-on-shakti-clusters/ |
| research | B3 | T3 | — † | — | fab | — | https://stackhpc.com/slurm-k8s-cluster.html |
| research | B3 | T3 | — † | — | fab | — | https://www.vcluster.com/blog/kubernetes-schedulers-vs-slurm |
| WILD | B2 | U | 2026 | url | fab | 4.2.2 | https://www.cloudoptimo.com/blog/kubernetes-ai-infrastructure-in-2026-gpu-scheduling-and-production-realities/ |
| WILD | B3 | U | — † | — | fab | — | https://collabnix.com/integrating-slurm-with-kubernetes-for-scalable-machine-learning-workloads/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/ajeetraina/integrating-slurm-with-kubernetes-for-scalable-machine-learning-workloads-1ik2 |
| WILD | B3 | U | — † | — | fab | 4.2.3 | https://medium.com/online-inference/slurm-on-kubernetes-sunk-modernizing-hpc-and-ai-workload-management-c945a40a28cf |
| WILD | B3 | U | — † | — | fab | 4.2.3 | https://medium.com/computing-systems-and-hardware-for-emerging/slurm-and-kubernetes-a-beginners-guide-to-resource-management-systems-5aeb735858cf |

### 4.2.2

**Q:** Heterogeneous pools (local GPUs, rented GPUs, hosted APIs) behind one abstraction?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://aibrix.readthedocs.io/latest/features/heterogeneous-gpu.html |
| primary | B3 | T2 | — † | — | cur | — | https://budecosystem.com/heterogenous-gpu-virtualisation-in-bud-ai-foundry/ |
| primary | B3 | T2 | — † | — | kim | — | https://developer.nvidia.com/blog/how-to-run-isolated-tenant-kubernetes-clusters-on-shared-gpu-infrastructure/ |
| primary | B3 | T2 | — † | — | kim | 4.2.6 | https://docs.skypilot.ai/en/stable/overview.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.yottalabs.ai/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Project-HAMi/HAMi/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/iannil/hetero-compute-router |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/InftyAI/Nebula |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/skypilot-org/skypilot/ |
| primary | B3 | T2 | — † | — | cur | — | https://project-hami.io/ |
| primary | B3 | T2 | — † | — | kim | — | https://virtual-kubelet.io/docs/providers/ |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.01579 |
| research | B2 | T3 | 2026 | exc | fab | — | https://shopify.engineering/skypilot |
| research | B2 | T3 | 2026 | url | fab | 4.2.5 | https://www.spheron.network/blog/kubernetes-gpu-orchestration-2026/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.15050 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://www.backend.ai/blog/2026-06-heterogeneous-gpu-operation |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.07472 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/html/2603.00356v1 |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.13201 |
| research | B3 | T3 | 2025-07 | url | fab | — | https://arxiv.org/pdf/2507.18748 |
| research | B3 | T3 | 2025-05 | url | fab | — | https://arxiv.org/pdf/2505.22864 |
| research | B3 | T3 | 2023-11 | url | fab | — | https://arxiv.org/pdf/2311.11514 |
| research | B3 | T3 | — † | — | kim | — | https://aditmodi.hashnode.dev/the-unified-gpu-platform-running-slurm-ray-and-kubernetes-inference-on-a-single-eks-cluster-without-scheduling-chaos |
| research | B3 | T3 | — † | — | fab | — | https://www.anyscale.com/blog/gpu-in-efficiency-in-ai-workloads |
| research | B3 | T3 | — † | — | fab | — | https://www.coreweave.com/blog/coreweave-adds-skypilot-support-for-effortless-multi-cloud-ai-orchestration |
| research | B3 | T3 | — † | — | fab | — | https://llm-d.ai/blog/heterogeneous-inference-3-vendor-sovereign-cluster |
| research | B3 | T3 | — † | — | kim | — | https://website.vcluster.com/uses/hybrid-kubernetes-gpu-cloud |
| WILD | B3 | U | 2025 | url | fab | — | https://jimmysong.io/blog/gpu-open-scheduling-hami-2025/ |

### 4.2.3

**Q:** Are profiles (4.1) portable across schedulers?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://docs.coreweave.com/products/sunk |
| primary | B3 | T2 | — † | — | fab | — | https://docs.coreweave.com/docs/products/sunk/tutorials/ray-on-sunk |
| primary | B3 | T2 | — † | — | kim | — | https://docs.ray.io/en/latest/cluster/kubernetes/k8s-ecosystem/kai-scheduler.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.skypilot.ai/en/latest/reference/kubernetes/examples/kueue-example.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.laiyagushi.com/run-ai/karta |
| primary | B3 | T2 | — † | — | kim | — | https://kueue.sigs.k8s.io/docs/concepts/multikueue/ |
| primary | B3 | T2 | — † | — | fab | — | https://www.nvidia.com/en-us/software/slurm/ |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.22691 |
| research | B3 | T3 | 2024-09 | url | fab | — | https://arxiv.org/html/2409.17070 |
| research | B3 | T3 | 2024-09 | url | fab | — | https://arxiv.org/pdf/2409.17070 |
| research | B3 | T3 | — † | — | kim | — | https://jingchaozhang.github.io/Gang-Scheduling-on-AKS-Volcano-vs-Kueue-vs-KAI/ |
| research | B3 | T3 | — † | — | fab | — | https://nebius.com/blog/posts/slurm-workload-manager |
| research | B3 | T3 | — † | — | fab | — | https://rafay.co/ai-and-cloud-native-blog/project-slinky-bringing-slurm-scheduling-to-kubernetes |
| research | B3 | T3 | — † | — | fab | — | https://www.wwt.com/blog/workload-management-and-orchestration-series-slurm-workload-manager |
| WILD | B2 | U | 2026-05-15 | url | fab | — | https://www.hpcwire.com/2026/05/15/slurm-vs-kubernetes-in-the-age-of-ai/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Slurm_Workload_Manager |

### 4.2.4

**Q:** Autoscale signals and limits.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-05-27 | url | fab | — | https://www.cncf.io/blog/2026/05/27/gpu-autoscaling-on-kubernetes-with-keda-building-an-external-scaler/ |
| core | B3 | T1 | — † | — | kim | — | https://agent-sandbox.sigs.k8s.io/docs/use-cases/examples/keda-scale-to-zero/ |
| primary | B3 | T2 | — † | — | cur | — | https://cloud.google.com/compute/docs/autoscaler/multiple-signals |
| primary | B3 | T2 | — † | — | cur | — | https://cloud.google.com/compute/docs/autoscaler/scaling-cloud-monitoring-metrics |
| primary | B3 | T2 | — † | — | cur | — | https://cloud.google.com/sdk/gcloud/reference/compute/instance-groups/managed/set-autoscaling |
| primary | B3 | T2 | — † | — | cur | — | https://docs.aws.amazon.com/cur/latest/userguide/split-cost-allocation-data-kubernetes-labels.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.cloud.google.com/compute/docs/labeling-resources |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kubernetes-sigs/agent-sandbox/blob/a53327b0/examples/keda-scale-to-zero/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://keda.sh/docs/2.20/reference/scaledobject-spec/ |
| primary | B3 | T2 | — † | — | kim | — | https://keda.sh/docs/2.20/concepts/scaling-deployments/ |
| primary | B3 | T2 | — † | — | kim | — | https://keda.sh/docs/2.20/scalers/prometheus/ |
| research | B1 | T3 | 2026-08-25 | exc | gpt | — | https://mvphub.tech/blog/can-a-serverless-mvp-scale-without-major-rework |
| research | B3 | T3 | — † | — | fab | — | https://cast.ai/blog/kubernetes-gpu-autoscaling/ |
| research | B3 | T3 | — † | — | fab | — | https://controlplane.com/blog/post/twelve-months-of-autoscaling-work-capacity-ai-and-keda |
| research | B3 | T3 | — † | — | fab | — | https://www.gmicloud.ai/en/blog/keda-autoscaling-ai-agents |
| WILD | B1 | U | 2026-06-26 | url | fab | — | https://devstarsj.github.io/2026/06/26/kubernetes-autoscaling-hpa-vpa-keda-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/kubernetes-ai-workloads-gpu-node-pools-autoscaling-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://devopsboys.com/blog/keda-event-driven-autoscaling-kubernetes-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://tech-insider.org/karpenter-vs-cluster-autoscaler-vs-keda-2026/ |
| WILD | B2 | U | 2026-05-13 | url | fab | — | https://codingwithtaz.blog/2026/05/13/production-ready-gpu-inference-autoscaling-on-eks-with-karpenter-keda-and-dragonfly/ |
| WILD | B3 | U | — † | — | fab | — | https://cloudnativenow.com/contributed-content/autoscaling-ai-workloads-on-kubernetes-with-keda-and-what-it-means-for-agentic-systems/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/autoscaling?l=go&o=desc&s=updated |
| WILD | B3 | U | — † | — | fab | — | https://stribog.com/blog/keda-descheduler-bare-metal-event-driven-autoscaling-scale-to-zero |

### 4.2.5

**Q:** GPU sharing/partitioning approach; node selection constraints.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://dra-driver-nvidia-gpu.sigs.k8s.io/docs/concepts/gpu-allocation/ |
| core | B3 | T1 | — † | — | cur kim | — | https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/ |
| primary | B3 | T2 | — † | — | kim | — | https://cloud.google.com/kubernetes-engine/docs/concepts/timesharing-gpus |
| primary | B3 | T2 | — † | — | cur fab | — | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/24.9/gpu-sharing.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.7/gpu-sharing.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/26.3/dra-intro-install.html |
| primary | B3 | T2 | — † | — | cur | — | https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/ |
| research | B1 | T3 | 2026-08-03 | url | fab | — | https://developers.redhat.com/articles/2026/08/03/multitenant-ai-inference-dynamic-resource-allocation-openshift |
| research | B2 | T3 | 2026-03-25 | url | fab | — | https://developers.redhat.com/articles/2026/03/25/dynamic-resource-allocation-goes-ga-red-hat-openshift-421-smarter-gpu |
| research | B2 | T3 | 2026-03-03 | url | fab | — | https://blog.aks.azure.com/2026/03/03/multi-instance-gpu-with-dra-on-aks |
| research | B3 | T3 | 2025-05-27 | url | fab | — | https://developers.redhat.com/articles/2025/05/27/boost-gpu-efficiency-kubernetes-nvidia-mig |
| research | B3 | T3 | — † | — | fab | — | https://cast.ai/blog/kubernetes-gpu-scheduling-bin-packing/ |
| research | B3 | T3 | — † | — | fab | — | https://cast.ai/blog/deploying-gpu-workload-with-dynamic-resource-allocation/ |
| research | B3 | T3 | — † | — | fab | — | https://www.naviteq.io/blog/sharing-a-gpu-on-eks-time-slicing-mps-mig-and-dra/ |
| research | B3 | T3 | — † | — | fab | — | https://www.nops.io/blog/gpu-sharing-in-kubernetes/ |
| research | B3 | T3 | — † | — | fab kim | — | https://scaleops.com/blog/kubernetes-gpu-sharing/ |
| research | B3 | T3 | — † | — | fab | — | https://scaleops.com/blog/kubernetes-dynamic-resource-allocation/ |
| research | B3 | T3 | — † | — | fab kim | — | https://www.vcluster.com/blog/diy-gpu-sharing-in-kubernetes |
| WILD | B1 | U | 2026-06-17 | url | fab | — | https://pkhamdee.blog/2026/06/17/gpu-sharing-on-kubernetes-time-slicing-mig-and-mps-compared-for-llm-workloads/ |
| WILD | B2 | U | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-dynamic-resource-allocation-gpu-dra/view |
| WILD | B3 | U | — † | — | fab | — | https://cloudrps.com/blog/fractional-gpus-kubernetes-mig-time-slicing-mps/ |

### 4.2.6

**Q:** Region placement for execution (4.1, 4.2): chosen by a placement engine for latency / failover, or pinned per profile to satisfy residency (10.5.4); is cross-region failover automatic?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/aws-samples/sample-multi-region-job-routing-on-eks/blob/main/docs/architecture.md |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/azure/aks/reliability-multi-region-deployment-models |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks-multi-region/aks-multi-cluster |
| research | B2 | T3 | 2026-06 | url | kim | — | https://arxiv.org/html/2606.15050v1 |
| research | B2 | T3 | 2026-06-02 | url | fab kim | 10.5.4 | https://tianpan.co/blog/2026/06/02/the-inference-region-your-data-residency-policy-forgot-to-pin |
| research | B2 | T3 | 2026-02 | url | kim | — | https://arxiv.org/html/2602.11688v1 |
| research | B3 | T3 | — † | — | kim | — | https://ai-tldr.dev/learn/production-llmops/llmops-fundamentals/multi-region-llm-failover/ |
| research | B3 | T3 | — † | — | fab | — | https://blaxel.ai/blog/ai-sandbox-data-residency-controls-regulated-industries |
| research | B3 | T3 | — † | — | kim | — | https://www.deepinspect.ai/blog/ai-gateway-multi-region-failover |
| research | B3 | T3 | — † | — | fab | — | https://www.plural.sh/blog/managing-multi-region-kubernetes-deployments-with-plural/ |
| research | B3 | T3 | — † | — | fab | — | https://techcommunity.microsoft.com/blog/azurearchitectureblog/reference-architecture-for-highly-available-multi-region-azure-kubernetes-servic/4490479 |
| research | B3 | T3 | — † | — | fab | — | https://vexxhost.com/blog/running-multi-region-kubernetes-on-openstack/ |
| WILD | B2 | U | 2026 | url | fab kim | 10.5.4 | https://www.digitalapplied.com/blog/ai-data-residency-architecture-patterns-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.factualminds.com/blog/aws-data-residency-sovereignty-guide-2026/ |
| WILD | B2 | U | 2026-03 | exc | fab | — | https://medium.com/@systemdesignwithsage/the-hidden-pitfalls-of-cross-region-data-pipelines-86b608b666ee |
| WILD | B2 | U | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-data-residency-controls-kubernetes/view |
| WILD | B2 | U | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-multi-zone-regional-resilience/view |
| WILD | B2 | U | 2026-01-30 | url | fab | — | https://oneuptime.com/blog/post/2026-01-30-multi-region-architecture/view |
| WILD | B3 | U | — † | — | fab | — | https://ekenechris.com/blog/architecting-multi-region-kubernetes-deployments-beyond-basic-replication/ |
| WILD | B3 | U | — † | — | fab | — | https://hidekazu-konishi.com/entry/amazon_bedrock_cross_region_inference_and_data_residency.html |
| WILD | B3 | U | — † | — | fab | — | https://www.teradata.com/insights/data-security/what-is-data-residency |

### 4.3.1

**Q:** Checkpoint owner: workflow engine (2.4), harness (3.1), or platform? Format versioned?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://cdn.jsdelivr.net/npm/pi-harness-runtime@1.1.28/packages/checkpoint/src/engine.ts |
| primary | B3 | T2 | — † | — | kim | — | https://docs.temporal.io/workflow-execution/event |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/MicrosoftDocs/semantic-kernel-docs/blob/main/agent-framework/workflows/checkpoints.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/microsoft/agent-framework/blob/de39be9e/python/packages/core/agent_framework/_workflows/_checkpoint.py |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/langchain-ai/langgraph/blob/4811d42614d0f9fea2e3b9de5467cec61b975666/libs/checkpoint/langgraph/checkpoint/base/__init__.py |
| primary | B3 | T2 | — † | — | cur kim | 4.3.6 | https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.workflowcheckpoint?view=agent-framework-python-latest |
| primary | B3 | T2 | — † | — | cur | — | https://microsoft-agent-framework.mintlify.app/workflows/checkpoints |
| primary | B3 | T2 | — † | — | kim | 4.3.5 | https://reference.langchain.com/python/langgraph/checkpoints |
| research | B3 | T3 | — † | — | kim | — | https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows |
| research | B3 | T3 | — † | — | kim | — | https://www.samuelfaj.com/en/blog/durable-execution-for-ai-agents-queue-or-workflow/ |
| WILD | B2 | U | 2026 | url | fab | — | https://agentspan.ai/blogs/best-ai-agent-runtime-platforms-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://appliedtechnologyindex.com/research/2026-comparative-analysis-durable-execution-infrastructure-ai-agents/ |
| WILD | B2 | U | 2026 | url | fab | — | https://appscale.blog/en/blog/durable-execution-llm-agents-temporal-langgraph-checkpointing-2026 |

### 4.3.2

**Q:** Boundary between engine durable state (2.4) and checkpoints here — one store or two?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://github.com/microsoft/agent-framework/discussions/2305 |
| primary | B3 | T2 | — † | — | fab kim | 4.3.6 | https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints |
| research | B3 | T3 | — † | — | kim | — | https://baeseokjae.github.io/posts/durable-execution-ai-agents-guide-2026/ |
| research | B3 | T3 | — † | — | kim | — | https://www.diagrid.io/blog/durable-execution-runtime-primitive-agents |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/langgraph-checkpointing-vs-temporal-durable-execution.html |
| research | B3 | T3 | — † | — | fab | — | https://www.indium.tech/7-state-persistence-strategies-ai-agents-2026/ |
| research | B3 | T3 | — † | — | kim | — | https://ranjankumar.in/state-architecture-agent-networks-langgraph-checkpointing |
| WILD | B3 | U | — † | — | fab | — | https://aijourn.com/beyond-the-agents-of-chaos-crisis-why-state-management-is-the-next-engineering-frontier-for-genai/ |

### 4.3.3

**Q:** Replay determinism: how non-deterministic model calls (3.2) and clock / timer reads (logical vs wall-clock time) are recorded and replayed.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur kim | cursor:2.5.5 | https://www.agentpatternscatalog.org/patterns/journaled-llm-call/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/gadda00/agentreplay |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/openwop/openwop/blob/main/spec/v1/replay.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/temporalio/documentation/blob/main/docs/encyclopedia/event-history/python.mdx |
| primary | B3 | T2 | — † | — | kim | — | https://temporal.io/blog/of-course-you-can-build-dynamic-ai-agents-with-temporal |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/abs/2607.16200 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.08275 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.09027 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/html/2505.17716v1 |
| research | B2 | T3 | 2026-04-12 | age | fab kim | — | https://tianpan.co/blog/2026-04-12-deterministic-replay-debugging-non-deterministic-ai-agents |
| research | B2 | T3 | 2026-04-12 | url | cur | cursor:2.5.5 | https://tianpan.co/blog/2026/04/12/deterministic-replay-debugging-non-deterministic-ai-agents |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2605.21997 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2604.08706v1 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/abs/2508.06412 |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/gabrielanhaia/stateful-agent-replay-deterministic-reruns-from-a-captured-trace-e9d |
| research | B3 | T3 | — † | — | cur | — | https://proofoftech.org/blog/deterministic-replay-agents/ |
| WILD | B1 | U | 2026-07 | age | fab | — | https://hosseinnejati.medium.com/temporal-workflows-deterministic-execution-replay-and-the-workflow-lifecycle-81e5b73d20f9 |
| WILD | B1 | U | 2026-07 | age | fab | — | https://medium.com/@sebuzdugan/stop-calling-real-llms-in-ci-record-the-decisions-replay-the-rest-5fdafd8b3455 |
| WILD | B3 | U | — † | — | cur | — | https://deepwiki.com/w20chen/ClawBox/4.3-model-gateway-trace-replay-and-inference |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@ThinkingLoop/replayable-agent-runs-the-debugging-trick-that-ships-f5460ebf390a |

### 4.3.4

**Q:** RPO/RTO per state class; DR test cadence.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/danielsmithdevelopment/ClawQL/blob/main/docs/security/security-best-practices-series/28-disaster-recovery-business-continuity.md |
| research | B1 | T3 | 2026-07-27 | url | kim | — | https://differentdev.com/blog/2026/07/27/how-often-test-disaster-recovery/ |
| research | B3 | T3 | — † | — | kim | — | https://67ailab.com/posts/day-09-ai-disaster-recovery/ |
| research | B3 | T3 | — † | — | cur | — | https://www.accrets.com/backupanddr/it-disaster-recovery-plan-template/ |
| research | B3 | T3 | — † | — | kim | — | https://aisuperthinkers.com/ai-agent-disaster-recovery/ |
| research | B3 | T3 | — † | — | kim | — | https://www.avepoint.com/blog/backup/what-are-rto-and-rpo-cloud |
| research | B3 | T3 | — † | — | cur | — | https://www.cloudsafe.com/dr-testing-frequency/ |
| research | B3 | T3 | — † | — | cur | — | https://www.fast-lta.de/en/blog/disaster-recovery-test-so-testen-sie-ihren-dr-plan |
| research | B3 | T3 | — † | — | cur | — | https://rivell.com/it-disaster-recovery-program/ |
| research | B3 | T3 | — † | — | cur | — | https://safeguard.sh/resources/blog/drp-testing |
| WILD | B2 | U | 2026 | url | fab | — | https://controlmonkey.io/resource/rto-vs-rpo/ |
| WILD | B2 | U | 2026 | url | fab | — | https://exodata.io/it-disaster-recovery-plan-template-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://khimananda.com/blog/rpo-and-rto-explained |
| WILD | B3 | U | — † | — | fab | — | https://checkthat.ai/answers/what-are-the-best-disaster-recovery-solutions |
| WILD | B3 | U | — † | — | fab | — | https://www.n-able.com/blog/rto-vs-rpo |
| WILD | B3 | U | — † | — | fab | — | https://www.sentinelone.com/cybersecurity-101/cloud-security/rto-vs-rpo/ |
| WILD | B3 | U | — † | — | fab | — | https://www.wanclouds.net/blog/others/what-are-disaster-recovery-rpo-and-rto |

### 4.3.5

**Q:** Storage backend behind a port — exit test.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://www.barebox.org/doc/latest/user/state.html |
| primary | B3 | T2 | — † | — | cur | — | https://code.letsbe.solutions/letsbe/pn-new-crm/raw/commit/0cc05f302f44dbdbbdb77e5b53e09b0c42c7aacb/tests/integration/storage-backend-swap.test.ts |
| primary | B3 | T2 | — † | — | cur | — | https://code.letsbe.solutions/letsbe/pn-new-crm/raw/branch/main/tests/integration/storage-backend-swap.test.ts |
| primary | B3 | T2 | — † | — | cur | — | https://code.letsbe.solutions/letsbe/pn-new-crm/src/commit/b2692839f15ba2e4aa499770a7e348aab364f883/tests/integration/storage-backend-swap.test.ts |
| primary | B3 | T2 | — † | — | cur | — | https://code.letsbe.solutions/letsbe/pn-new-crm/src/commit/32b57354ad2888ab0902404e4fa8890b186a78ae/tests/unit/storage/backup-export.test.ts |
| primary | B3 | T2 | — † | — | fab | — | https://deepwiki.com/opentofu/opentofu/5.1-backend-architecture |
| primary | B3 | T2 | — † | — | kim | — | https://docs.langchain.com/oss/python/langgraph/checkpointers |
| primary | B3 | T2 | — † | — | kim | — | https://docs.langchain.com/langsmith/custom-checkpointer |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/kvcache-ai/Mooncake/blob/c251eefa/mooncake-store/tests/e2e/storage_backend_e2e_test.cpp |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/langchain-ai/langgraph/blob/4a86705b/libs/checkpoint/README.md |
| research | B3 | T3 | — † | — | fab | — | https://github.com/tweedegolf/storage-abstraction |
| research | B3 | T3 | — † | — | fab | — | https://mintlify.wiki/get-convex/convex-backend/architecture/persistence |
| WILD | B2 | U | 2026 | url | fab | — | https://medium.com/@alexendrascott01/running-stateful-applications-on-kubernetes-a-2026-guide-for-scalable-reliable-back-end-systems-9ed469e0ef01 |

### 4.3.6

**Q:** Checkpoint compatibility across code / model / prompt version changes.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | exc | kim | — | https://github.com/microsoft/agent-framework/pull/7636 |
| primary | B2 | T2 | 2026 | url | fab kim | — | https://learn.microsoft.com/en-us/agent-framework/support/upgrade/python-2026-significant-changes |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-framework/pull/3744 |
| research | B3 | T3 | — † | — | cur | — | https://aiprompts.cloud/versioning-prompts-and-models-a-governance-playbook-for-cont |
| research | B3 | T3 | — † | — | cur | — | https://codenicely.in/blog/startups/saas/ai-prompt-versioning-cheatsheet |
| research | B3 | T3 | — † | — | cur | — | https://promptassay.ai/blog/how-to-version-prompts-2026-guide |
| research | B3 | T3 | — † | — | cur | — | https://www.respan.ai/articles/prompt-versioning |
| WILD | B3 | U | — † | — | fab | — | https://blog.ljga.net/posts/ai-image-generation/ai-image-generation-checkpoints/ |
| WILD | B3 | U | — † | — | fab | — | https://checkpoint.engineer/category/releases/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/ggml-org/llama.cpp/issues/24055 |
| WILD | B3 | U | — † | — | fab | — | https://proxyle.com/blog/a-guide-to-model-checkpoints-in-stable-diffusion/ |

### 4.3.7

**Q:** On resume from a checkpoint (4.3.1), is the caller's authorization re-validated against current policy (2.2), or does the job carry the credential and decision captured at checkpoint time?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B2 | T3 | 2026-03 | url | kim | — | https://arxiv.org/pdf/2603.20625 |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/zira125/your-ai-agent-restarted-did-its-credentials-survive-too-4mop |
| research | B3 | T3 | — † | — | kim | — | https://fondsites.com/ai-agents/guidebooks/agent-checkpoints-resumable-work/ |
| research | B3 | T3 | — † | — | kim | — | https://nhimg.org/faq/how-do-organisations-know-when-an-agentic-ai-recovery-process-is-actually-trustw/ |
| research | B3 | T3 | — † | — | kim | — | https://qubittool.com/blog/ai-agent-memory-persistence-architecture |
| WILD | B1 | U | 2026-09 | age | fab | — | https://permit.substack.com/p/is-2026-the-year-check-point-dies |
| WILD | B3 | U | — † | — | fab | — | https://passitexams.com/articles/salesforce-security-updates-2026/ |

### 4.4.1

**Q:** Memory types (short-term, long-term, episodic, shared) and the store behind each.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B1 | T3 | 2026-06-21 | url | kim | — | https://www.marktechpost.com/2026/06/21/the-7-types-of-agent-memory-a-technical-guide-for-ai-engineers/ |
| research | B2 | T3 | 2026 | url | fab | — | https://www.taskade.com/blog/ai-agent-memory |
| research | B2 | T3 | 2026-04 | age | fab | — | https://www.analyticsvidhya.com/blog/2026/04/memory-systems-in-ai-agents/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2507.02097 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2309.14365 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2412.06531 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2212.02098 |
| research | B3 | T3 | — † | — | fab | — | https://atlan.com/know/types-of-ai-agent-memory/ |
| research | B3 | T3 | — † | — | kim | — | https://augmentable.ai/blog/state-of-ai-agent-memory-2026 |
| research | B3 | T3 | — † | — | kim | — | https://www.cognee.ai/cognitive-architectures-for-language-agents-explained |
| research | B3 | T3 | — † | — | cur | — | https://datapace.ai/blog/ai-agent-memory-layer-architecture-guide-2026 |
| research | B3 | T3 | — † | — | kim | — | https://www.digitalapplied.com/blog/agent-memory-architectures-vector-graph-episodic |
| research | B3 | T3 | — † | — | fab | — | https://github.com/TsinghuaC3I/Awesome-Memory-for-Agents |
| research | B3 | T3 | — † | — | kim | — | https://www.ibm.com/think/topics/ai-agent-memory |
| research | B3 | T3 | — † | — | cur | — | https://jatinbansal.com/ai-engineering/memory-cognitive-taxonomy/ |
| research | B3 | T3 | — † | — | fab | — | https://machinelearningmastery.com/beyond-short-term-memory-the-3-types-of-long-term-memory-ai-agents-need/ |
| research | B3 | T3 | — † | — | kim | — | https://mastra.ai/articles/agent-memory |
| research | B3 | T3 | — † | — | kim | — | https://memanto.ai/blog/four-kinds-of-agent-memory |
| research | B3 | T3 | — † | — | cur | — | https://www.memoryplugin.com/wiki/what-is-ai-memory.html |
| research | B3 | T3 | — † | — | cur | — | https://www.rpatech.ai/blogs/ai-memory/ |
| WILD | B3 | U | — † | — | cur | — | https://www.webmd.com/alzheimers/types-of-memory |

### 4.4.2

**Q:** Retrieval port — no standard exists: define read / write / search / forget.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://agentflow.10xscale.ai/docs/reference/python/memory-stores |
| primary | B3 | T2 | — † | — | kim | — | https://docs.nvidia.com/agentiq/latest/api/aiq/memory/interfaces/index.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/dibenedetto/a2m-protocol/blob/main/README.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/mthamil107/memorywire/blob/main/docs/paper/memorywire-paper.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/mthamil107/memorywire |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/deep-thinking-llc/open-agent-memory-protocol/blob/main/spec/v1/oamp-v1.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mem0ai/mem0/blob/main/mem0-plugin/skills/mem0/references/api-reference.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/genieincodebottle/agentic-memory/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/smysle/agent-memory |
| research | B2 | T3 | 2026 | url | fab | — | https://aishwaryasrinivasan.substack.com/p/all-you-need-to-know-about-rag-in |
| research | B2 | T3 | 2026 | url | fab | — | https://www.buildfastwithai.com/blogs/collection/rag-vector-databases |
| research | B2 | T3 | 2026 | url | fab | — | https://dev.to/suraj_khaitan_f893c243958/-rag-in-2026-a-practical-blueprint-for-retrieval-augmented-generation-16pp |
| research | B3 | T3 | — † | — | kim | — | https://www.alibabacloud.com/blog/agent-memory-why-persistent-recall-needs-more-than-a-vector-database_603532 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2412.17942 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2506.16444 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2602.15874 |
| research | B3 | T3 | — † | — | cur | — | https://neoneye.github.io/agent-memory-atlas/patterns/pluggable-memory-provider/ |
| research | B3 | T3 | — † | — | kim | — | https://plur.ai/blog/mem0-vs-letta-vs-zep/ |
| WILD | B3 | U | — † | — | fab | — | https://aiamastery.substack.com/p/lesson-16-vector-store-and-rag |
| WILD | B3 | U | — † | — | fab | — | https://jobsbyculture.com/blog/rag-architecture-guide-2026 |

### 4.4.3

**Q:** Relationship to workspace (3.4): is memory a workspace component or separate?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/serejke/ai-agents-theory/blob/main/patterns/workspace.md |
| primary | B3 | T2 | — † | — | kim | — | https://java.agentscope.io/v2/en/docs/building-blocks/context.html |
| primary | B3 | T2 | — † | — | kim | — | https://java.agentscope.io/v2/en/docs/others/going-to-production.html |
| research | B2 | T3 | 2026 | url | fab | — | https://powerdrill.ai/blog/best-ai-agent-memory-solutions |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2601.11655 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2604.23878 |

### 4.4.4

**Q:** Cache layer (response / prompt cache) separate from memory?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://developers.openai.com/api/docs/guides/prompt-caching |
| research | B3 | T3 | — † | — | cur | — | https://www.adaptiverecall.com/ai-cost-optimization/caching-strategies.php |
| research | B3 | T3 | — † | — | kim | — | https://aistackcurrent.com/ai-engineering/prompt-caching-for-llm-applications/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2601.06007v2 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2502.07776 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2602.21257 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2605.24914 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2511.19477 |
| research | B3 | T3 | — † | — | cur kim | — | https://barkingiguana.com/writing/prompt-caching-versus-response-caching-on-bedrock/ |
| research | B3 | T3 | — † | — | cur | — | https://engineering-playbook.vercel.app/agentic/agent-memory |
| research | B3 | T3 | — † | — | cur | — | https://medium.com/@contextlabsllc/ai-knowledge-systems-from-ephemeral-context-to-durable-memory-07a5da34d03c |
| research | B3 | T3 | — † | — | fab | — | https://sparkco.ai/blog/mastering-claude-prompt-caching-techniques-for-2025 |
| research | B3 | T3 | — † | — | cur | — | https://thegustafson.com/blog/context-engineering |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalocean.com/blog/prompt-caching-with-digital-ocean |
| WILD | B3 | U | — † | — | fab | — | https://ngrok.com/blog/prompt-caching |

### 4.4.5

**Q:** Eviction, TTL, cross-agent sharing rules.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026 | url | fab | — | https://icml.cc/virtual/2026/poster/66783 |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/evictions.html |
| primary | B3 | T2 | — † | — | kim | — | https://neo4j.com/labs/agent-memory/explanation/multi-agent-sharing/ |
| research | B2 | T3 | 2026-05-21 | url | kim | — | https://hindsight.vectorize.io/blog/2026/05/21/agent-memory-consolidation |
| research | B2 | T3 | 2026-04-21 | url | kim | — | https://hindsight.vectorize.io/guides/2026/04/21/guide-building-multi-agent-systems-with-shared-memory |
| research | B2 | T3 | 2026-03-31 | age | fab | — | https://oneuptime.com/blog/post/2026-03-31-redis-volatile-ttl-eviction-policy/view |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2511.02230v4 |
| research | B3 | T3 | — † | — | fab | — | https://github.com/sgl-project/sglang/issues/24656 |
| research | B3 | T3 | — † | — | kim | — | https://www.techaheadcorp.com/blog/agent-memory-state/ |
| WILD | B3 | U | — † | — | fab | — | https://algomaster.io/learn/system-design/cache-eviction-policies |
| WILD | B3 | U | — † | — | fab | — | https://www.designgurus.io/blog/cache-eviction-strategies |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/web-tech-journals/cache-eviction-policies-explained-lru-vs-lfu-vs-fifo-vs-ttl-5daf6b50af39 |

### 4.4.6

**Q:** Is content pulled into context by tool calls or retrieval (8.3) tagged with a trust level distinct from operator instructions, and does the harness (3.1) prevent instruction-shaped strings in untrusted content from acting as directives?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | 10.1.8 | https://devblogs.microsoft.com/agent-framework/fides/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-framework/blob/b3f2e539/python/samples/02-agents/security/FIDES_DEVELOPER_GUIDE.md |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/agent-framework/agents/security |
| research | B1 | T3 | 2026-09 | url | kim | — | https://startdebugging.net/2026/09/information-flow-control-to-block-prompt-injection-in-agents/ |
| research | B2 | T3 | 2026 | url | fab kim | 10.1.8 | https://www.sysdig.com/learn-cloud-native/prompt-injection |
| research | B2 | T3 | 2026-04 | url | fab | 10.1.8 | https://arxiv.org/pdf/2604.12986 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2605.31042 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2409.19091 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2605.17634 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2505.14534 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2606.09204 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2512.06914 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2605.24421 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2609.00470v1 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2204.08592 |
| research | B3 | T3 | — † | — | kim | — | https://sajid-nazeer.medium.com/an-agent-does-not-become-secure-because-it-has-a-polite-system-prompt-agent-security-with-fides-10e214949a82 |
| research | B3 | T3 | — † | — | fab | 10.1.8 | https://www.vectra.ai/topics/prompt-injection |
| WILD | B3 | U | — † | — | fab | — | https://christian-schneider.net/blog/rag-security-forgotten-attack-surface/ |

## 5. Assurance & Completion

### 5.1.1

**Q:** Quality gate definition format; declared per workflow (2.4), per job class, or by policy (2.2)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | 2023-12 | url | fab | — | https://autom-devops-en.doc.squashtest.com/2023-12/devops/qualitygate.html |
| primary | B3 | T2 | 2023-10 | url | fab | — | https://autom-devops-en.doc.squashtest.com/2023-10/devops/qualitygate.html |
| primary | B3 | T2 | — † | — | cur | — | https://www.opentestfactory.org/impl/reference/qualitygate-syntax.html |
| primary | B3 | T2 | — † | — | cur | — | https://www.opentestfactory.org/guides/qualitygate.html |
| primary | B3 | T2 | — † | — | cur | — | https://www.opentestfactory.org/learn-opentf-orchestrator/contexts.html |
| primary | B3 | T2 | — † | — | cur | — | https://www.opentestfactory.org/tools/opentf-ctl/qualitygate.html |
| primary | B3 | T2 | — † | — | fab | — | https://opentestfactory.org/impl/reference/qualitygate-syntax.html |
| research | B3 | T3 | — † | — | kim | — | https://www.augmentcode.com/guides/quality-gates-software-development |
| research | B3 | T3 | — † | — | kim | — | https://www.frankx.ai/blog/agent-skill-standard-evaluated-workflows-2026 |
| research | B3 | T3 | — † | — | kim | — | https://www.kategos.ai/articles/multi-pass-schema-enforcement-ai-governance |
| research | B3 | T3 | — † | — | kim | — | https://qaskills.sh/blog/release-gates-yaml-team-policy-schema |
| WILD | B1 | U | 2026-07 | exc | fab | — | https://medium.com/@rajesh.yemul_42550/ai-quality-gates-f913d94544b2 |
| WILD | B2 | U | 2026 | exc | fab | — | https://khimananda.com/blog/sonarqube-code-quality-and-security-gates |
| WILD | B2 | U | 2026 | exc | fab | — | https://noopsschool.com/blog/quality-gates/ |
| WILD | B3 | U | — † | — | fab | — | https://deepwiki.com/SonarSource/sonarqube/6.5-quality-gates |
| WILD | B3 | U | — † | — | fab | — | https://inferensys.com/glossary/data-observability-and-quality-posture/data-quality-metrics/data-quality-gate |
| WILD | B3 | U | — † | — | fab | — | https://sgsystemsglobal.com/glossary/in-process-quality-gates/ |
| WILD | B3 | U | — † | — | fab | — | https://www.techtarget.com/searchsoftwarequality/definition/quality-gate |
| WILD | B3 | U | — † | — | fab | — | https://testkube.io/glossary/quality-gates |
| WILD | B3 | U | — † | — | fab | — | https://testrigor.com/blog/software-quality-gates/ |

### 5.1.2

**Q:** Validator port: tests, security scans, schema checks, LLM-as-judge — all behind one pass / fail / evidence interface?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Lewis-404/agent-ci-verify/blob/main/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/venkatapgummadi/ascend |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/siddhivinayak-sk/ai-artifact-risk-validator/blob/main/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kenithphilip/Tessera |
| primary | B3 | T2 | — † | — | kim | 5.1.3 | https://github.com/OrionArchitekton/schemafit |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/docs/evaluation/evaluation-methods/llm-as-a-judge |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.01153 |
| research | B2 | T3 | 2026 | exc | fab | — | https://deepeval.com/blog/llm-as-a-judge |
| research | B2 | T3 | 2026 | url | fab | — | https://judge2026.github.io/ |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/pyhacksecgp/i-built-a-sastdast-triage-pipeline-because-scanner-noise-was-killing-my-signal-4126 |
| research | B3 | T3 | — † | — | fab | — | https://www.trendmicro.com/vinfo/us/security/news/managed-detection-and-response/llm-as-a-judge-evaluating-accuracy-in-llm-security-scans |
| WILD | B2 | U | 2026 | url | fab | — | https://www.braintrust.dev/articles/best-llm-guardrails-security-testing-tools-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://filterprompt.io/blog/llm-security-testing-guide |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/llm-testing-2026-methods-strategies/ |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/what-is-llm-input-output-validation-2026/ |
| WILD | B2 | U | 2026 | exc | fab | 7.3.4 | https://futureagi.com/blog/llm-as-a-judge/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://labelyourdata.com/articles/llm-as-a-judge |
| WILD | B2 | U | 2026 | url | fab | — | https://qaskills.sh/blog/llm-guardrails-testing-guide-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.siemba.io/owasp-top-10-llm-security-testing |
| WILD | B3 | U | — † | — | fab | — | https://www.adaline.ai/blog/llm-as-a-judge-reliability-bias |
| WILD | B3 | U | — † | — | cur | — | https://github.com/takoneko8/adjudge |
| WILD | B3 | U | — † | — | cur | — | https://github.com/vinsoc-cyber/VulnHunterX |
| WILD | B3 | U | — † | — | cur | — | https://github.com/accuknox/codeassure-cli |
| WILD | B3 | U | — † | — | cur | — | https://github.com/raccioly/websec-validator |

### 5.1.3

**Q:** Scanner choices pluggable; results normalized (SARIF for code scans)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2023-08-28 | exc | fab | — | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.pdf |
| core | B3 | T1 | 2023-08-28 | exc | fab | — | https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/sarif-v2.1.0-errata01-os.html |
| core | B3 | T1 | 2020-03-27 | exc | gpt | — | https://www.oasis-open.org/standard/sarifv2-1-os/ |
| core | B3 | T1 | — † | — | fab | — | https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html |
| core | B3 | T1 | — † | — | fab | — | https://docs.oasis-open.org/sarif/sarif/v2.1.0/cs01/sarif-v2.1.0-cs01.html |
| core | B3 | T1 | — † | — | fab | — | https://docs.oasis-open.org/sarif/sarif/v2.0/csprd01/sarif-v2.0-csprd01.html |
| core | B3 | T1 | — † | — | gpt | — | https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/csd01/sarif-v2.1.0-errata01-csd01-redlined.html |
| core | B3 | T1 | — † | — | fab | — | https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=sarif |
| core | B3 | T1 | — † | — | fab | — | https://www.oasis-open.org/committees/sarif/charter.php |
| core | B3 | T1 | — † | — | kim gpt | — | https://sarifweb.azurewebsites.net/ |
| primary | B3 | T2 | — † | — | fab | — | https://developer.harness.io/docs/security-testing-orchestration/custom-scanning/ingest-sarif-data/ |
| primary | B3 | T2 | — † | — | fab | — | https://developer.harness.io/docs/security-testing-orchestration/custom-scanning/custom-ingest-reference/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.github.com/en/code-security/concepts/code-scanning/sarif-files |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.github.com/en/code-security/reference/code-scanning/codeql/codeql-cli/sarif-output |
| primary | B3 | T2 | — † | — | cur kim | — | https://github.com/tinydarkforge/SecGate |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Su1ph3r/vinculum |
| primary | B3 | T2 | — † | — | kim | — | https://github.laiyagushi.com/Martinez1991/quorum-sec-scan |
| primary | B3 | T2 | — † | — | cur | — | https://pypi.org/project/vibeguard-cli/1.1.10/ |
| primary | B3 | T2 | — † | — | cur | — | https://pypi.org/project/shun-secscan/0.19.0/ |
| research | B1 | T3 | 2026-07-20 | exc | gpt | — | https://www.quantakrypto.com/standards/sarif-code-scanning |
| research | B3 | T3 | — † | — | fab | — | https://www.sonarsource.com/resources/library/sarif/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://spacelift.io/blog/terraform-scanning-tools |
| WILD | B3 | U | — † | — | fab | — | https://accuknox.com/blog/aspm-platforms-sarif |
| WILD | B3 | U | — † | — | cur | — | https://github.com/VISHNU0906/gatekeeper |
| WILD | B3 | U | — † | — | cur | — | https://github.laiyagushi.com/ochmunkh/Tatar-Kuber |
| WILD | B3 | U | — † | — | fab | — | https://secportal.io/scanner-info/scanner-output-formats |

### 5.1.4

**Q:** Failure routing: retry, replan (2.3), human, reject.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.08214 |
| research | B2 | T3 | 2026-04-27 | url | kim | — | https://tianpan.co/blog/2026/04/27/replan-dont-retry-agent-tool-errors |
| research | B3 | T3 | — † | — | cur | — | https://agentic-design.ai/patterns/workflow-orchestration/graph-state-machines |
| research | B3 | T3 | — † | — | kim | — | https://agentiveaiagents.com/ai-agent-error-handling-best-practices/ |
| research | B3 | T3 | — † | — | cur | — | https://aiskillcerts.com/concepts/agentic-architecture/multi-agent-error-handling-and-routing |
| research | B3 | T3 | — † | — | cur | — | https://argonsys.com/microsoft-cloud/library/when-ai-agents-fail-engineering-reliable-recovery-with-microsoft-foundry/ |
| research | B3 | T3 | — † | — | kim | 10.3.1 | https://dev.to/samcorp_388df23e8f0e61ab6/building-an-agent-that-actually-handles-failure-b2e |
| research | B3 | T3 | — † | — | cur | — | https://ecoaai.com/agent-orchestration-state-machine-not-dag/ |
| research | B3 | T3 | — † | — | kim | — | https://www.linkedin.com/pulse/how-build-fallback-logic-ai-powered-automation-without-treating-every-iuizf |
| research | B3 | T3 | — † | — | kim | — | https://theneuralbase.com/agent-patterns/learn/intermediate/escalation-patterns/ |
| WILD | B1 | U | 2026-08 | exc | fab | — | https://levelup.gitconnected.com/engineering-reliable-coding-agent-loops-control-flow-verification-retries-and-stop-conditions-f002d2dc168c |
| WILD | B2 | U | 2026 | url | fab | — | https://www.bestaiweb.ai/how-to-implement-retry-fallback-and-self-correction-loops-in-ai-agents-in-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://chiraghasija.cc/posts/building-ai-agents-that-work-production-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://evomap.ai/blog/agentic-workflows-2026-how-they-work |
| WILD | B2 | U | 2026 | url | fab | — | https://www.explainx.ai/blog/ai-agent-loop-architecture-triggers-retries-checkpoints-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://fast.io/resources/ai-agent-retry-patterns/ |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/agent-architecture-patterns-2026/ |
| WILD | B2 | U | 2026 | exc | fab | 10.3.1 | https://www.prismocode.io/ai-agent-retry-policies/ |
| WILD | B3 | U | — † | — | fab | — | https://cohesivity.ai/blog/ai-agent-failure-recovery-retries-checkpoints-human-approval |
| WILD | B3 | U | — † | — | fab | — | https://editorialge.com/human-in-the-loop-design-for-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/NousResearch/hermes-agent/issues/344 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@vasanthancomrads/handling-failures-in-agent-based-workflows-c0fd9489b2ee |

### 5.1.5

**Q:** Adversarial testing (prompt-injection resistance, jailbreak, tool-misuse probes) as a distinct validator type (5.1.2) and a required gate before promotion (7.3, 7.4), or only implicit in generic security scans?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/danielmadii/AgentSecBench |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/vamsisudhakaran1/release-gate |
| primary | B3 | T2 | — † | — | fab | — | https://www.promptfoo.dev/docs/red-team/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.promptfoo.dev/docs/red-team/owasp-agentic-ai/ |
| research | B1 | T3 | 2026-09-04 | exc | gpt | — | https://agilelabs.com/testing-ai-agents-for-prompt-injection |
| research | B2 | T3 | 2026 | exc | fab | — | https://dl.acm.org/doi/10.1145/3803628.3807972 |
| research | B2 | T3 | 2026 | exc | fab | — | https://www.group-ib.com/resources/knowledge-hub/jailbreak-detection/ |
| research | B2 | T3 | 2026-03-18 | exc | gpt | — | https://www.hackerone.com/press-release/hackerone-launches-agentic-prompt-injection-testing-ai-vulnerabilities-surge-540 |
| research | B2 | T3 | 2026-03-18 | exc | gpt | — | https://www.hackerone.com/blog/agentic-prompt-injection-testing |
| research | B3 | T3 | 2025-05 | url | fab | — | https://arxiv.org/abs/2505.04806 |
| research | B3 | T3 | 2025-05 | url | fab | — | https://arxiv.org/pdf/2505.04806 |
| research | B3 | T3 | — † | — | kim | — | https://accelate.ai/blog/red-team-ai-agent-before-launch |
| research | B3 | T3 | — † | — | kim | — | https://www.straiker.ai/blog/top-6-ai-red-teaming-and-adversarial-testing-tools |
| WILD | B2 | U | 2026 | exc | fab | — | https://appsecsanta.com/ai-security-tools/llm-red-teaming |
| WILD | B2 | U | 2026 | url | fab | — | https://kili-technology.com/blog/llm-red-teaming-in-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://medium.com/@muhammadishtiaqh25/ai-red-teaming-in-2026-a-practical-guide-to-prompt-hacking-jailbreaks-and-defending-llm-9f07a7227d66 |
| WILD | B2 | U | 2026 | url | fab | — | https://sureprompts.com/blog/prompt-injection-defense-complete-guide-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://ziosec.com/blog/ai-jailbreak-techniques-in-2026-a-complete-technical-guide-ziosec |
| WILD | B3 | U | 2025 | url | fab | — | https://futureagi.com/blog/jailbreaking-chatgpt-2025/ |
| WILD | B3 | U | — † | — | fab | — | https://gist.github.com/kibotu/c06f54d6fbc4705e886a50fb2e59e6ae |
| WILD | B3 | U | — † | — | fab | — | https://purplesec.us/resources/ai-security-glossary/jailbreaking/ |

### 5.1.6

**Q:** IP / license provenance: is generated code checked for verbatim reproduction of licensed material (license classifier, code similarity) as a validation gate (5.1.2), with the result attached to provenance (5.2.2)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://blog.codacy.com/codacy-just-teased-its-new-gpl-license-scanner-for-ai-code |
| primary | B3 | T2 | — † | — | kim | — | https://pypi.org/project/provenire/0.1.2/ |
| research | B3 | T3 | — † | — | kim | — | https://aigovernance.com/controls/ai-generated-code-license-compliance |
| research | B3 | T3 | — † | — | kim | — | https://blog.codacy.com/code-review-is-dead-why-ai-generated-code-needs-verification-not-human-approval |
| research | B3 | T3 | — † | — | fab | — | https://fossa.com/blog/generative-ai-and-software-development-copyright-law-and-license-compliance/ |
| research | B3 | T3 | — † | — | kim | — | https://newworld.cloud/automating-legal-compliance-checks-for-llm-produced-code-in- |
| research | B3 | T3 | — † | — | kim | — | https://www.re-entry.ai/blog/ai-generated-code-license-compliance-guide |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.aimadetools.com/blog/who-owns-ai-generated-code/ |
| WILD | B2 | U | 2026 | url | fab | — | https://baeseokjae.github.io/posts/ai-code-security-scanning-tools-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/ai-generated-code-liability-legal-risk-copyright-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.cloudapper.ai/enterprise-ai/ai-generated-code-open-source-license-risk-enterprise/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/pickuma/ai-license-laundering-how-code-generators-strip-open-source-obligations-2i0m |
| WILD | B3 | U | — † | — | fab | — | https://www.fortegrp.com/insights/understanding-code-provenance |
| WILD | B3 | U | — † | — | fab | — | https://paddo.dev/blog/ai-code-copyright-void/ |
| WILD | B3 | U | — † | — | fab | — | https://www.systemshardening.com/articles/cicd/ai-code-license-compliance/ |
| WILD | B3 | U | — † | — | fab | — | https://www.virtuosoqa.com/post/testing-ai-generated-code-regulated-industries |

### 5.2.1

**Q:** Approval: automatic vs human; where humans interact (AG-UI events, 1.1)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | gpt | 5.3.1 | https://docs.ag-ui.com/sdk/js/core/events |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/ag-ui/latest/ag_ui/client/interrupts/struct.ResumeBuilder.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.showcase.copilotkit.ai/ag-ui/drafts/interrupts |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ag-ui-protocol/ag-ui/blob/821b8c227c6fe7b78de2c8259173dd7cbbdf181b/sdks/dotnet/plugins/ag-ui-dotnet/skills/agui-dotnet-human-in-the-loop/SKILL.md |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/ag-ui-protocol/ag-ui/discussions/158 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ag-ui-protocol/ag-ui/blob/main/integrations/langgraph/typescript/README.md |
| primary | B3 | T2 | — † | — | cur fab | — | https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/human-in-the-loop |
| primary | B3 | T2 | — † | — | cur | — | https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/workflows |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/human-in-the-loop |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/lukaswalter/agent-frontends-with-ag-ui-streaming-tool-calls-and-human-approval-4e00 |
| research | B3 | T3 | — † | — | fab | — | https://techcommunity.microsoft.com/blog/appsonazureblog/ag-ui-the-future-of-agent-driven-user-interfaces/4515769 |
| research | B3 | T3 | — † | — | kim | — | https://threadplane.ai/docs/ag-ui/guides/interrupts |
| WILD | B2 | U | 2026-05-28 | url | fab | — | https://zylos.ai/research/2026-05-28-agentic-ux-frontend-design-patterns-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://www.calpcc.com/learning-center/ai-governance/human-approval-for-ai-actions/ |
| WILD | B3 | U | — † | — | cur | — | https://tessl.io/registry/skills/github/ag-ui-protocol/ag-ui/agui-dotnet-human-in-the-loop |

### 5.2.2

**Q:** Provenance record format: in-toto attestation / SLSA provenance / W3C PROV — which?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2023-05 | url | cur fab | 6.3.2 | https://slsa.dev/blog/2023/05/in-toto-and-slsa |
| core | B3 | T1 | 2013-04-30 | exc | cur kim | — | https://www.w3.org/TR/prov-o/ |
| core | B3 | T1 | 2013-04-30 | exc | cur | — | https://www.w3.org/TR/prov-dm/Overview.html |
| core | B3 | T1 | — † | — | fab gpt | — | https://github.com/in-toto/attestation/blob/main/spec/predicates/provenance.md |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/slsa-framework/slsa/blob/main/spec/build-provenance.md |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/in-toto/attestation |
| core | B3 | T1 | — † | — | cur kim gpt | — | https://slsa.dev/spec/v1.1/provenance |
| core | B3 | T1 | — † | — | fab kim gpt | 6.3.2 | https://slsa.dev/spec/v0.1/provenance |
| core | B3 | T1 | — † | — | fab kim | — | https://slsa.dev/spec/draft/build-provenance |
| core | B3 | T1 | — † | — | fab | — | https://slsa.dev/spec/v1.0/distributing-provenance |
| core | B3 | T1 | — † | — | fab | — | https://slsa.dev/attestation-model |
| core | B3 | T1 | — † | — | gpt | — | https://slsa.dev/spec/draft/provenance |
| core | B3 | T1 | — † | — | kim | — | https://www.w3.org/TR/prov-dm/ |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.08363 |
| research | B2 | T3 | 2026-04-25 | url | kim | — | https://zylos.ai/research/2026-04-25-agent-identity-provenance-signed-audit-trails/ |
| research | B2 | T3 | 2026-03 | url | fab | 6.3.2 | https://arxiv.org/pdf/2603.02512 |
| research | B3 | T3 | 2023-12-28 | url | fab | — | https://mikael.barbero.tech/blog/post/2023-12-28-slsa-and-in-toto/ |
| research | B3 | T3 | — † | — | fab | — | https://www.legitsecurity.com/blog/slsa-provenance-blog-series-part-2-deeper-dive-into-slsa-provenance |
| research | B3 | T3 | — † | — | cur fab | 6.3.2 | https://secure-pipelines.com/ci-cd-security/artifact-provenance-attestations-slsa-in-toto/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@rrey94/slsa-its-all-about-provenance-attestation-09a83b7b9de7 |

### 5.2.3

**Q:** Signing of admitted outputs (Sigstore)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab gpt | — | https://docs.sigstore.dev/cosign/verifying/verify/ |
| core | B3 | T1 | — † | — | fab gpt | — | https://docs.sigstore.dev/quickstart/quickstart-cosign/ |
| core | B3 | T1 | — † | — | cur | — | https://docs.sigstore.dev/about/bundle/ |
| core | B3 | T1 | — † | — | gpt | — | https://docs.sigstore.dev/cosign/verifying/ |
| core | B3 | T1 | — † | — | cur | — | https://github.com/sigstore/architecture-docs/blob/main/client-spec.md |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/sigstore/docs/blob/main/content/en/cosign/verifying/verify.md |
| primary | B3 | T2 | — † | — | fab | — | https://blog.sigstore.dev/cosign-3-0-available/ |
| primary | B3 | T2 | — † | — | cur fab gpt | — | https://docs.sigstore.dev/cosign/signing/overview/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.sigstore.dev/cosign/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.sigstore.dev/cosign/signing/signing_with_containers/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.sigstore.dev/cosign/signing/other_types/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/actions/attest-build-provenance/blob/03fc44ed67c67cf2fb577046feff97b214b91b0b/README.md |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/sigstore/cosign |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/sigstore/cosign/releases |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/sigstore/cosign/blob/main/CHANGELOG.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/sigstore/sigstore-a2a |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/always-further/agent-sign |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/cezexPL/agent-passport-standard/blob/main/spec/model-provenance.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/sigstore/sigstore-go/blob/main/docs/signing.md |
| primary | B3 | T2 | — † | — | cur | — | https://www.npmjs.com/package/@actions/attest |
| primary | B3 | T2 | — † | — | gpt | — | https://sigstore.github.io/sigstore-python/signing/ |
| research | B2 | T3 | 2026-05 | exc | kim | — | https://crashoverride.com/resources/knowledge-base/provenance/cryptographic-provenance-agent-output |
| research | B3 | T3 | — † | — | fab | — | https://cycode.com/blog/securing-artifacts-keyless-signing-with-sigstore-and-ci-mon/ |
| research | B3 | T3 | — † | — | kim | — | https://fast.io/resources/ai-agent-output-attestation/ |
| research | B3 | T3 | — † | — | fab | — | https://goreleaser.com/blog/cosign-v3/ |
| WILD | B2 | U | 2026-05 | url | fab | — | https://blogs.perl.org/users/timothy_legge/2026/05/signing-cpan-releases-with-sigstore.html |
| WILD | B3 | U | — † | — | fab | — | https://www.freshports.org/security/cosign |

### 5.2.4

**Q:** Admission decisions auditable and reversible?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/yzhao062/auditable |
| primary | B3 | T2 | — † | — | kim | 5.2.5 | https://github.com/makerchecker/MakerChecker |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/agent-governance-toolkit/adr/0030-action-bound-approval-protocol/ |
| primary | B3 | T2 | — † | — | gpt | 5.3.4 | https://mvp-scale.com/pricing |
| primary | B3 | T2 | — † | — | gpt | — | https://mvp-scale.com/security |
| research | B2 | T3 | 2026-05 | url | cur | — | https://arxiv.org/html/2605.17998v1 |
| research | B3 | T3 | — † | — | cur | — | https://www.deepinspect.ai/blog/how-to-build-a-defensible-ai-audit-trail |
| research | B3 | T3 | — † | — | cur | — | https://kevinchamplin.com/blog/if-there-s-no-reversible-decision-record-it-s-not-ai-for-regulated-work |
| research | B3 | T3 | — † | — | cur | — | https://tenetai.dev/blog/what-is-ai-decision-ledger |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.admissions.uga.edu/?p=1548 |
| WILD | B2 | U | 2026 | exc | fab | — | https://heybob.ai/blog/ai-agent-audit-trail/ |
| WILD | B2 | U | 2026 | url | fab kim | 10.2.5 | https://www.kognitos.com/blog/ai-audit-trail-requirements-2026-checklist/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.miniorange.com/blog/ai-agent-audit-trail/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.securityscientist.net/blog/12-questions-and-answers-about-audit-defensibility-of-ai-assisted-decisions-complete-guide-for-2026/ |
| WILD | B2 | U | 2026-06 | exc | fab | — | https://velt.dev/blog/audit-trails-ai-decisions-regulators-require |
| WILD | B2 | U | 2026-03 | url | fab | — | https://www.cdcr.ca.gov/bph/wp-content/uploads/sites/161/2026/03/pv-CY-2026-Suitability-DataTemplate-for-WP.pdf |
| WILD | B2 | U | 2026-02-27 | url | fab | — | https://www.gov.uk/government/publications/the-archbishops-school-27-february-2026 |
| WILD | B3 | U | 2024-07-05 | exc | fab | — | https://registrar.unl.edu/faculty-and-staff/faculty-and-staff-tutorials/staff-tutorials/registration-audit-trail |
| WILD | B3 | U | 2023-02-13 | url | fab | — | https://committees.provost.ncsu.edu/undergraduate-admissions/wp-content/uploads/sites/2/MINUTES_Undergraduate-Admissions-Committee_February_13_2023.pdf |
| WILD | B3 | U | 2022-04-05 | url | fab | — | https://committees.provost.ncsu.edu/undergraduate-admissions/wp-content/uploads/sites/2/MINUTES_Undergraduate-Admissions-Committee_April-5-2022.pdf |
| WILD | B3 | U | — † | — | fab | — | https://democracy.brighton-hove.gov.uk/ieDecisionDetails.aspx?Id=2030 |
| WILD | B3 | U | — † | — | cur | — | https://github.com/lexseasson/agentic-decision-ledger |
| WILD | B3 | U | — † | — | fab | — | https://github.com/yzhao062/awesome-auditable-ai |
| WILD | B3 | U | — † | — | fab | — | https://www.ivycoach.com/the-ivy-coach-blog/college-admissions/when-do-college-decisions-come-out/ |
| WILD | B3 | U | — † | — | fab | — | https://mightybot.ai/blog/what-are-ai-agent-audit-trails/ |
| WILD | B3 | U | — † | — | fab | — | https://training.hr.ufl.edu/instructionguides/myadmissions/releasing_decisions.pdf |

### 5.2.5

**Q:** Approval authority: is the required approver role scaled to the output's risk tier, and is self-approval by the requesting identity prevented?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.promptise.com/mcp/server/approval-gates/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/sammysltd/makerchecker/blob/main/docs/concepts.md |
| research | B3 | T3 | — † | — | kim | — | https://ai-infrastructure.net/agent-risk-tiered-approval/ |
| research | B3 | T3 | — † | — | kim | — | https://www.arthur.ai/column/human-in-the-loop-governance-for-ai-agents |
| research | B3 | T3 | — † | — | fab | — | https://www.kovrr.com/blog-post/multi-agent-ai-systems-separation-of-duties |
| WILD | B2 | U | 2026 | exc | fab | — | http://devsecopsschool.com/blog/separation-of-duties/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.pactvera.com/delegated-signing-controls-in-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.toriihq.com/articles/segregation-of-duties |
| WILD | B3 | U | — † | — | fab | — | https://anchor-defense.com/articles/federal-workflow-orchestration-segregation-of-duties/ |
| WILD | B3 | U | — † | — | fab | — | https://www.kenfromfinance.com/glossary/delegation-of-authority-matrix-ap |
| WILD | B3 | U | — † | — | fab | — | https://latchworkflow.com/blog/approval-design-high-risk-operations |
| WILD | B3 | U | — † | — | fab | — | https://madslow.medium.com/separation-of-duties-structuring-authority-to-reduce-risk-01680fd9d373 |
| WILD | B3 | U | — † | — | fab | — | https://www.nexusap.com/blog/segregation-of-duties-accounts-payable |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/faq/why-does-separation-of-duties-reduce-fraud-and-insider-threat-risk-in-cybersecur/ |
| WILD | B3 | U | — † | — | fab | — | https://www.securends.com/blog/segregation-vs-separation-of-duties-whats-the-difference/ |
| WILD | B3 | U | — † | — | fab | — | https://www.securityscientist.net/blog/12-questions-and-answers-about-separation-of-duties-in-changes/ |
| WILD | B3 | U | — † | — | fab | — | https://www.siit.io/blog/role-based-access-controls |
| WILD | B3 | U | — † | — | fab | — | https://umbrex.com/resources/frameworks/organization-frameworks/delegation-of-authority-doa-framework/ |

### 5.3.1

**Q:** Return contract mirrors each entry type: API response (1.1), AG-UI event (1.1), A2A task completion (1.5), bus event (1.3).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/a2aproject/A2A/blob/main/docs/topics/life-of-a-task.md |
| primary | B3 | T2 | — † | — | cur | — | https://a2a-protocol.org/latest/sdk/python/api/a2a.server.agent_execution.agent_executor.html |
| primary | B3 | T2 | — † | — | fab | — | https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-a2a-protocol-contract.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/google/A2A/blob/7b900e77/docs/tutorials/python/4-agent-executor.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ag-ui-protocol/ag-ui/blob/daadb5f3/integrations/a2a/typescript/src/agent.ts |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.00887 |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/google-cloud/a2a-deep-dive-getting-real-time-updates-from-ai-agents-a28d60317332 |
| WILD | B3 | U | — † | — | fab | — | https://agentwiki.org/ag_ui_protocol |
| WILD | B3 | U | — † | — | cur | — | https://github.com/shashikanth-gs/a2a-wrapper/blob/main/packages/core/README.md |
| WILD | B3 | U | — † | — | cur | — | https://github.com/a2aproject/A2A/issues/763 |

### 5.3.2

**Q:** Notification channels behind one port (email, chat, webhook)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://github.com/novuhq/novu |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/GabrielBBaldez/notify-hub |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/gabrielbbaldez/notify-hub |
| primary | B3 | T2 | — † | — | kim | — | https://github.laiyagushi.com/novuhq/novu |
| primary | B3 | T2 | — † | — | kim | — | https://github.laiyagushi.com/richardfcampos/notify-hub |
| primary | B3 | T2 | — † | — | kim | — | https://www.npmjs.com/package/omni-notify-mcp |
| research | B2 | T3 | 2026 | exc | fab kim | — | https://www.sequenzy.com/blog/best-notification-apis-for-ai-agents |
| research | B3 | T3 | — † | — | cur | — | https://www.kingsleyonoh.com/foundry/webhook-ingestion-engine |
| WILD | B2 | U | 2026 | url | fab | — | https://www.pistack.xyz/posts/novu-vs-apprise-vs-ntfy-self-hosted-notification-infrastructure-guide-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.sequenzy.com/blog/best-email-tools-with-webhook-support |
| WILD | B2 | U | 2026-03-15 | url | fab | — | https://blog.balaskas.gr/2026/03/15/i-replaced-every-notification-service-with-apprise/ |
| WILD | B3 | U | — † | — | fab | — | https://www.chatwoot.com/features/channels |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/reactjsguru/novu-open-source-notification-infrastructure-478a |
| WILD | B3 | U | — † | — | fab | — | https://docs.openwebui.com/features/administration/webhooks/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Google_Chat |
| WILD | B3 | U | — † | — | fab | — | https://engagespot.co/ |
| WILD | B3 | U | — † | — | cur | — | https://github.com/RyanMoreau/webhook-gateway |
| WILD | B3 | U | — † | — | cur | — | https://github.com/prime-optimal/whook |
| WILD | B3 | U | — † | — | cur | — | https://github.com/gopackx/go-notification |
| WILD | B3 | U | — † | — | fab | — | https://openapps.pro/apps/novu |
| WILD | B3 | U | — † | — | fab | — | https://semaphoreui.com/roadmap/flexible-notification-system |
| WILD | B3 | U | — † | — | fab | — | https://support.netenrich.com/hc/en-us/articles/9870876496669-Notification-Channels |
| WILD | B3 | U | — † | — | fab | — | https://www.vonage.com/resources/articles/unified-messaging-platform/ |
| WILD | B3 | U | — † | — | fab | — | https://www.vonage.com/resources/articles/multi-channel-notifications/ |

### 5.3.3

**Q:** Artifact delivery: link vs inline; expiry.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://www.alibabacloud.com/help/en/oss/user-guide/how-to-obtain-the-url-of-a-single-object-or-the-urls-of-multiple-objects |
| primary | B3 | T2 | — † | — | fab | — | https://developer.fabric.inc/product-agent/api-reference/artifacts/get-artifact |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/prescriptive-guidance/latest/presigned-url-best-practices/overview.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/sdk-for-kotlin/api/latest/sagemaker/aws.sdk.kotlin.services.sagemaker.model/-authorized-url |
| primary | B3 | T2 | — † | — | kim | — | https://docs.aws.amazon.com/pdfs/prescriptive-guidance/latest/presigned-url-best-practices/presigned-url-best-practices.pdf |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/aws/aws-sdk-go-v2/issues/1557 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/mlflow/mlflow/issues/21037 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/phenobarbital/ai-parrot/blob/main/docs/operations/infographic_csp_and_signed_urls.md |
| research | B3 | T3 | — † | — | cur | — | https://www.boxtoolpro.com/blog/data-uri-vs-image-url |
| research | B3 | T3 | — † | — | cur kim | — | https://dev.to/kongkong1/deliver-large-agent-artifacts-with-signed-urls-not-giant-json-responses-kp5 |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/zylahmorn61835/presigned-object-access-explained-expired-generated-image-urls-in-support-saas-1dpc |
| research | B3 | T3 | — † | — | kim | — | http://research.ivision.com/signed-sealed-delivered-secure.html |
| research | B3 | T3 | — † | — | kim | — | https://software-engineer-blog.com/content/how-safe-is-a-60-minute-signed-url-the-link-is-the-credential?id=172 |
| WILD | B2 | U | 2026-02-12 | url | fab | — | https://oneuptime.com/blog/post/2026-02-12-generate-presigned-urls-temporary-s3-access/view |
| WILD | B3 | U | — † | — | fab | — | https://blog.vnykmshr.com/writing/presigned-urls-static-sites/ |
| WILD | B3 | U | — † | — | fab | — | https://cloudwebschool.com/docs/aws/storage-services/s3-signed-urls/ |
| WILD | B3 | U | — † | — | fab | — | https://community.alteryx.com/discussion/1360373/download-with-aws-presigned-url |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/zhizhiarv/important-notes-on-s3-presigned-url-expiration-3ga9 |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/kerryconvery/how-would-you-handle-expirying-presigned-urls-on-the-frontend-2nak |
| WILD | B3 | U | — † | — | fab | — | https://forum.gitlab.com/tag/artifact/116 |
| WILD | B3 | U | — † | — | cur | — | https://github.com/taihei-05/siglume-api-sdk/blob/main/docs/artifact-delivery.md |
| WILD | B3 | U | — † | — | cur | — | https://github.com/inference-gateway/typescript-adk/blob/main/src/artifacts/minio-storage.ts |
| WILD | B3 | U | — † | — | fab | — | https://teamcity-support.jetbrains.com/hc/en-us/community/posts/360000000470-S3-plugin-fails-to-download-artefacts-due-to-presigned-URLs-are-expired |

### 5.3.4

**Q:** SLA measurement point.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://agentping.io/docs/concepts/runs-and-events |
| primary | B3 | T2 | — † | — | cur | — | https://docs.infraon.io/infraon-help/infinity-user-guide/sla-management/metric |
| primary | B3 | T2 | — † | — | cur | — | https://learn.lxc.liferay.com/w/dxp/low-code/workflow/using-workflows/using-workflow-metrics |
| primary | B3 | T2 | — † | — | kim | — | https://telemetry.sh/event-schemas/ai-agent-run-completed |
| research | B2 | T3 | 2026-03-22 | url | kim | — | https://zylos.ai/research/2026-03-22-sre-ai-agent-systems-observability-incident-response/ |
| research | B3 | T3 | 2024-06 | url | fab | — | https://arxiv.org/pdf/2406.09093 |
| research | B3 | T3 | — † | — | kim | — | https://agentmodeai.com/agentic-ai-sla-architecture/ |
| research | B3 | T3 | — † | — | fab | — | https://www.atlassian.com/incident-management/kpis/sla-vs-slo-vs-sli |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/custodiaadmin/measuring-and-maintaining-sla-reliability-for-ai-agent-workflows-1dmn |
| research | B3 | T3 | — † | — | fab | — | https://firehydrant.com/blog/sla-vs-slo/ |
| research | B3 | T3 | — † | — | fab | — | https://www.ibm.com/think/topics/service-level-objective |
| research | B3 | T3 | — † | — | fab | — | https://incident.io/blog/slo-sla-sli |
| research | B3 | T3 | — † | — | fab | — | https://newrelic.com/blog/observability/what-are-slos-slis-slas |
| research | B3 | T3 | — † | — | fab | — | https://www.splunk.com/en_us/blog/learn/sla-vs-sli-vs-slo.html |
| research | B3 | T3 | — † | — | cur | — | https://vdf.ai/blog/on-prem-ai-agent-platform-slos/ |
| research | B3 | T3 | — † | — | cur fab kim | — | https://wavect.io/blog/ai-agent-sla-template/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/ai-agent-sla-uptime-accuracy-response-time-guarantee-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://dataopsschool.com/blog/latency-sla/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://fivenines.io/blog/sla-monitoring-tools/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://nurbak.com/en/blog/slo-vs-sla/ |
| WILD | B3 | U | — † | — | fab | — | https://www.emergentmind.com/topics/slo-aware-llm-inference-slai |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Service-level_objective |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Service_level_indicator |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9054995 |

## 6. Observe

### 6.1.1

**Q:** OpenTelemetry as the only emission contract; GenAI semantic conventions adopted (which version), and since they are still experimental, what is the policy for absorbing breaking attribute renames?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-09-07 | exc | gpt | — | https://opentelemetry.netlify.app/blog/2026/genai-observability/ |
| core | B1 | T1 | 2026-06-12 | exc | cur fab gpt | cursor:6.1.1 | https://github.com/open-telemetry/semantic-conventions-genai |
| core | B3 | T1 | — † | — | fab kim | — | https://github.com/open-telemetry/semantic-conventions/releases |
| core | B3 | T1 | — † | — | fab | — | https://github.com/open-telemetry/semantic-conventions-genai/releases |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md |
| core | B3 | T1 | — † | — | cur kim gpt | 6.1.4 10.5.2 cursor:6.1.1 | https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/ |
| core | B3 | T1 | — † | — | fab gpt | — | https://opentelemetry.io/docs/specs/semconv/gen-ai/ |
| core | B3 | T1 | — † | — | gpt | — | https://opentelemetry.io/docs/specs/semconv/gen-ai/mcp/ |
| core | B3 | T1 | — † | — | gpt | — | https://opentelemetry.io/docs/specs/semconv/ |
| primary | B2 | T2 | 2026 | url | fab | — | https://opentelemetry.io/blog/2026/genai-observability/ |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/docs/latest/genai/tracing/opentelemetry/genai-semconv/ |
| research | B1 | T3 | 2026-08-13 | exc | cur kim | cursor:6.1.1 | https://particula.tech/blog/opentelemetry-genai-semantic-conventions-stable |
| research | B1 | T3 | 2026-07-17 | exc | cur fab kim | 10.3.7 cursor:6.1.1 | https://john-hodge.com/blog/opentelemetry-genai-semantic-conventions/ |
| research | B2 | T3 | 2026 | exc | fab | — | https://openobserve.ai/blog/opentelemetry-semantic-conventions/ |
| research | B2 | T3 | 2026-06 | exc | cur kim | cursor:6.1.1 | https://praesidia.ai/blog/opentelemetry-genai-semantic-conventions-status |
| research | B2 | T3 | 2026-05-09 | url | cur fab | 10.3.7 cursor:6.1.1 | https://greptime.com/blogs/2026-05-09-opentelemetry-genai-semantic-conventions |
| research | B3 | T3 | — † | — | kim | — | https://clickhouse.com/resources/engineering/opentelemetry-semantic-conventions |
| research | B3 | T3 | — † | — | cur fab | 6.1.4 cursor:6.1.1 | https://openobserve.ai/blog/opentelemetry-genai-semantic-conventions/ |
| WILD | B1 | U | 2026-07-16 | exc | cur fab | 10.3.7 cursor:6.1.1 | https://dev.to/azena-ai/opentelemetrys-genai-semantic-conventions-are-not-stable-yet-heres-what-actually-shipped-in-2026-3mke |
| WILD | B2 | U | 2026 | exc | fab | — | https://callsphere.ai/blog/vw3c-opentelemetry-genai-conventions-ai-agents-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://techbytes.app/posts/opentelemetry-genai-agent-semconv-cheat-sheet-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://veraexmachina.com/tech/opentelemetry-genai-agent-observability-production/ |
| WILD | B2 | U | 2026-02-28 | url | fab | — | https://zylos.ai/research/2026-02-28-opentelemetry-ai-agent-observability/ |
| WILD | B3 | U | — † | — | fab | — | https://community.dynatrace.com/t5/AI/OpenLLMetry-semantic-conventions-are-now-part-of-OpenTelemetry/td-p/267984 |
| WILD | B3 | U | — † | — | fab | 10.3.7 | https://dev.to/x4nent/opentelemetry-genai-semantic-conventions-the-standard-for-llm-observability-1o2a |
| WILD | B3 | U | — † | — | fab | 10.3.7 | https://hidekazu-konishi.com/entry/opentelemetry_genai_semantic_conventions_guide.html |

### 6.1.2

**Q:** Backend (Langfuse) reached via OTLP only, or vendor SDK (a leak)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/library-guidelines.md |
| core | B3 | T1 | — † | — | cur gpt | 6.1.5 | https://opentelemetry.io/docs/specs/otlp/ |
| core | B3 | T1 | — † | — | cur | — | https://opentelemetry.io/docs/specs/otel/protocol/exporter/ |
| core | B3 | T1 | — † | — | cur | — | https://opentelemetry.io/docs/concepts/instrumentation/libraries |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/orgs/langfuse/discussions/11540 |
| primary | B3 | T2 | — † | — | fab kim gpt | — | https://langfuse.com/integrations/native/opentelemetry/migration-to-v4 |
| primary | B3 | T2 | — † | — | fab kim gpt | — | https://langfuse.com/integrations/native/opentelemetry |
| primary | B3 | T2 | — † | — | fab kim | — | https://langfuse.com/resources/engineering/opentelemetry-languages |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/docs/api-and-data-platform/features/public-api |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/docs/compatibility |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/faq/all/existing-otel-setup |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/guides/cookbook/otel_integration_openllmetry |
| primary | B3 | T2 | — † | — | gpt | — | https://langfuse.com/guides/cookbook/example_data_migration |
| primary | B3 | T2 | — † | — | gpt | — | https://langfuse.com/faq/all/deprecated-api-migration |
| primary | B3 | T2 | — † | — | fab | — | https://launchdarkly.com/docs/tutorials/otel-llm-practical-guide-with-langfuse |
| primary | B3 | T2 | — † | — | cur | — | https://opentelemetry.io/docs/languages/go/instrumentation/ |
| research | B3 | T3 | — † | — | kim | — | https://pydantic.dev/articles/best-langfuse-alternatives |
| research | B3 | T3 | — † | — | kim | — | https://twistag.com/thinking/ai-agent-observability |
| WILD | B3 | U | — † | — | fab | — | https://github.com/ferraroroberto/local-llm-hub/issues/4 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@sharanharsoor/opentelemetry-for-llmops-how-langfuse-achieved-universal-multi-language-support-without-building-782d843adf3c |

### 6.1.3

**Q:** Trace context propagation across AG-UI (1.1), A2A (1.5), MCP (3.5) hops — W3C Trace Context.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/open-telemetry/semantic-conventions/blob/e126ea9105b15912ccd80deab98929025189b696/docs/gen-ai/mcp.md |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/open-telemetry/opentelemetry-specification/blob/main/oteps/0066-separate-context-propagation.md |
| core | B3 | T1 | — † | — | cur kim | — | https://modelcontextprotocol.org/seps/414-request-meta |
| core | B3 | T1 | — † | — | gpt | — | https://opentelemetry.io/docs/specs/otel/context/api-propagators/ |
| core | B3 | T1 | — † | — | kim | — | https://www.w3.org/TR/trace-context/ |
| primary | B2 | T2 | 2026 | exc | cur fab | cursor:0.8.2 | https://last9.io/blog/opentelemetry-context-propagation/ |
| primary | B3 | T2 | — † | — | cur | — | https://classic.docs.ag2.ai/latest/docs/user-guide/tracing/remote-agents/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.ag2.ai/latest/docs/user-guide/tracing/remote-agents/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.dapr.io/operations/observability/tracing/w3c-tracing-overview/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/modelcontextprotocol/python-sdk/pull/2381 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/brunovicco/a2a-otel-kit |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/kagent-dev/kagent/blob/890ca100/go/core/internal/a2a/trace.go |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agentgateway/agentgateway/pull/2520 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/finemcp/finemcp/blob/main/client/propagation.go |
| primary | B3 | T2 | — † | — | fab | — | https://opentelemetry.io/docs/concepts/context-propagation/ |
| primary | B3 | T2 | — † | — | fab | — | https://opentelemetry.io/docs/concepts/signals/traces/ |
| primary | B3 | T2 | — † | — | cur | — | https://py.sdk.modelcontextprotocol.io/run/opentelemetry/ |
| research | B1 | T3 | 2026-07-28 | exc | cur | — | https://dreaming.press/posts/how-to-trace-an-mcp-tool-call-w3c-trace-context.html |
| research | B2 | T3 | 2026 | url | cur | — | https://cubeapm.com/blog/how-to-instrument-mcp-servers-with-opentelemetry/ |
| research | B2 | T3 | 2026-04-06 | url | fab | — | https://developers.redhat.com/articles/2026/04/06/distributed-tracing-agentic-workflows-opentelemetry |
| research | B2 | T3 | 2026-03 | url | fab | 10.1.10 | https://arxiv.org/pdf/2603.24775 |
| research | B2 | T3 | 2026-02-02 | url | fab | — | https://oneuptime.com/blog/post/2026-02-02-opentelemetry-context-propagation/view |
| research | B2 | T3 | 2026-01 | url | fab | 9.1 9.4 9.5 | https://arxiv.org/pdf/2601.02371 |
| research | B3 | T3 | — † | — | cur kim | — | https://mortalapps.com/agents/protocols/w3c-trace-context-a2a-propagation/ |
| research | B3 | T3 | — † | — | fab | — | https://openobserve.ai/blog/opentelemetry-context-propagation/ |
| research | B3 | T3 | — † | — | fab | — | https://uptrace.dev/opentelemetry/context-propagation |
| WILD | B2 | U | 2026 | exc | fab | — | https://gingerlabs.ai/blog/mcp-2026-roadmap-stateless-transport-agent-communication-enterprise-authentication |
| WILD | B2 | U | 2026-04-19 | url | fab | — | https://tianpan.co/blog/2026/04/19/distributed-tracing-agent-service-boundaries |
| WILD | B3 | U | — † | — | fab | — | https://focused.io/lab/agent-traces-need-to-cross-the-mcp-boundary |

### 6.1.4

**Q:** Sampling policy; redaction in spans; retention.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-01-12 | exc | cur fab kim | — | https://opentelemetry.io/docs/security/handling-sensitive-data/ |
| core | B3 | T1 | — † | — | cur | cursor:6.1.1 | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-events.md |
| primary | B3 | T2 | 2025 | url | fab | — | https://opentelemetry.io/blog/2025/sampling-milestones/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.dynatrace.com/docs/ingest-from/opentelemetry/collector/use-cases/redact |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.honeycomb.io/send-data/opentelemetry/collector/handle-sensitive-information |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/v0.149.0/processor/redactionprocessor/README.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/193e049b/processor/redactionprocessor/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/redactionprocessor |
| primary | B3 | T2 | — † | — | fab | — | https://opentelemetry.io/docs/zero-code/obi/configure/collector-receiver/ |
| primary | B3 | T2 | — † | — | fab | — | https://opentelemetry.io/docs/collector/components/processor/ |
| research | B2 | T3 | 2026-04 | exc | cur | — | https://medium.com/@alokrahuldevops/day-106-ottl-in-depth-what-it-is-how-it-works-and-why-it-matters-for-ai-workloads-2362f9abbb34 |
| research | B2 | T3 | 2026-02-06 | url | fab | — | https://github.com/oneuptime/blog/tree/master/posts/2026-02-06-data-retention-policies-opentelemetry |
| research | B2 | T3 | 2026-02-06 | url | cur | — | https://oneuptime.com/blog/post/2026-02-06-prevent-sensitive-data-leakage-auto-instrumentation/view |
| research | B2 | T3 | 2026-02-06 | url | fab | — | https://oneuptime.com/blog/post/2026-02-06-data-retention-policies-opentelemetry/view |
| research | B2 | T3 | 2026-02-06 | url | fab | — | https://oneuptime.com/blog/post/2026-02-06-redaction-processor-opentelemetry-collector/view |
| research | B3 | T3 | — † | — | cur fab | — | https://www.dash0.com/guides/scrubbing-sensitive-data-with-opentelemetry |
| research | B3 | T3 | — † | — | fab | — | https://www.dash0.com/knowledge/opentelemetry-tracing |
| research | B3 | T3 | — † | — | kim | — | https://www.dash0.com/guides/opentelemetry-redaction-processor |
| research | B3 | T3 | — † | — | fab | — | https://www.fiddler.ai/blog/opentelemetry-ai-observability-guide |
| research | B3 | T3 | — † | — | fab | — | https://last9.io/blog/redacting-sensitive-data-in-opentelemetry-collector/ |
| research | B3 | T3 | — † | — | cur | — | https://www.systemshardening.com/articles/observability/otel-pii-leakage/ |
| WILD | B2 | U | 2026 | exc | fab | 10.7.2 | https://projectsupply.in/blog/opentelemetry-distributed-tracing-2026 |
| WILD | B3 | U | — † | — | fab | 10.7.2 | https://maketocreate.com/opentelemetry-genai-tracing-ai-agents-without-leaking-pii/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@alokrahuldevops/day-107-sampling-strategies-in-opentelemetry-what-they-are-why-they-matter-and-why-ai-311ee7e9676a |

### 6.1.5

**Q:** Exit test: second backend receiving the same OTLP stream.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-05-06 | exc | gpt | — | https://opentelemetry.io/docs/compatibility/migration/ |
| core | B3 | T1 | — † | — | cur | — | https://opentelemetry.io/docs/collector/configuration/ |
| primary | B3 | T2 | — † | — | fab | 10.7.2 | https://opentelemetry.io/ |
| primary | B3 | T2 | — † | — | fab | — | https://opentelemetry.io/docs/collector/quick-start/ |
| primary | B3 | T2 | — † | — | fab | 10.7.2 | https://opentelemetry.io/docs/collector/ |
| research | B2 | T3 | 2026 | exc | fab | — | https://www.apica.io/blog/what-is-opentelemetry-a-comprehensive-guide/ |
| research | B2 | T3 | 2026 | exc | fab | — | https://openobserve.ai/blog/opentelemetry-backends-otlp-support/ |
| research | B2 | T3 | 2026-02-17 | url | kim | — | https://agentgateway.dev/blog/2026-02-17-agentgateway-langfuse-integration/ |
| research | B2 | T3 | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-otel-collector-exporters-backends/view |
| research | B2 | T3 | 2026-02-06 | url | cur fab | — | https://oneuptime.com/blog/post/2026-02-06-multi-backend-export-opentelemetry-collector/view |
| research | B2 | T3 | 2026-02-06 | url | cur fab | — | https://oneuptime.com/blog/post/2026-02-06-fan-out-pipelines-opentelemetry-collector/view |
| research | B2 | T3 | 2026-02-06 | url | fab kim | — | https://oneuptime.com/blog/post/2026-02-06-otel-fan-out-pipeline-multiple-backends/view |
| research | B3 | T3 | — † | — | fab | — | https://www.dash0.com/guides/opentelemetry-collector |
| research | B3 | T3 | — † | — | kim | — | https://www.datadoghq.com/knowledge-center/opentelemetry/ |
| research | B3 | T3 | — † | — | kim | — | https://growthengineer.ai/blog/ai-agent-observability-otel-langfuse |
| research | B3 | T3 | — † | — | kim | — | https://maniak.io/articles/2026-02-14-llm-observability-agentgateway-langfuse/ |
| research | B3 | T3 | — † | — | cur | — | https://www.parseable.com/blog/opentelemetry-collector-configuration |
| research | B3 | T3 | — † | — | cur | — | https://uptrace.dev/opentelemetry/collector/config |
| WILD | B2 | U | 2026 | exc | fab | — | https://dev.to/ottoaria/opentelemetry-in-2026-the-complete-guide-to-observability-for-modern-backends-jpl |
| WILD | B3 | U | — † | — | fab | — | https://blog.devops.dev/a-guide-to-opentelemetry-collector-dcc8e8123115 |
| WILD | B3 | U | — † | — | fab | — | https://devhelm.io/blog/otel-collector-explained |

### 6.2.1

**Q:** Schema for eval results, datasets, human feedback; linked to trace IDs (6.1).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/Arize-ai/openinference/blob/main/spec/annotations.md |
| primary | B3 | T2 | — † | — | cur | — | https://www.confident-ai.com/docs/human-in-the-loop/collect-feedback |
| primary | B3 | T2 | — † | — | kim | — | https://evalevalai.com/projects/every-eval-ever/ |
| primary | B3 | T2 | — † | — | cur fab | — | https://langfuse.com/docs/evaluation/scores/data-model |
| primary | B3 | T2 | — † | — | cur fab | cursor:6.2.4 | https://langfuse.com/docs/observability/features/user-feedback |
| primary | B3 | T2 | — † | — | cur fab | cursor:6.2.4 | https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/docs/query-traces |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/guides/human-in-the-loop-scoring |
| primary | B3 | T2 | — † | — | fab | — | https://langfuse.com/docs/evaluation/overview |
| primary | B3 | T2 | — † | — | cur | — | https://mlflow.org/docs/latest/genai/concepts/feedback/ |
| research | B2 | T3 | 2026 | exc | fab kim | 6.2.3 | https://futureagi.com/blog/llm-eval-feedback-loop-design-2026/ |
| research | B2 | T3 | 2026 | exc | fab | 6.2.2 7.1.3 | https://futureagi.com/blog/llm-evaluation-playbook-2026/ |
| research | B2 | T3 | 2026 | exc | fab | 7.1.3 8.1.6 10.6.6 | https://galtea.ai/blog/llm-evaluation-complete-guide |
| research | B2 | T3 | 2026-03 | exc | fab | 10.6.6 | https://www.openlayer.com/blog/llm-evaluation-metrics-complete-guide |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2603.23806v2 |
| research | B3 | T3 | — † | — | kim | — | https://latitude.so/blog/llm-feedback-collection-annotations-enhance |
| research | B3 | T3 | — † | — | kim | — | https://markaicode.com/langsmith-annotation-queues-human-feedback/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.braintrust.dev/articles/best-human-in-the-loop-llm-evaluation-platforms-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://medium.com/online-inference/the-best-llm-evaluation-tools-of-2026-40fd9b654dce |
| WILD | B2 | U | 2026 | exc | fab | 7.1.3 10.6.6 | https://medium.com/@nairmilind3/llm-evaluation-in-2026-e631a78c67dc |
| WILD | B2 | U | 2026 | exc | fab | — | https://qaskills.sh/blog/langfuse-llm-observability-guide-2026 |
| WILD | B3 | U | — † | — | cur | — | https://www.youtube.com/watch?v=20U6INQJyyU |

### 6.2.2

**Q:** No broad standard exists; which dataset format is adopted (JSONL contract)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://developers.openai.com/cookbook/examples/evaluation/getting_started_with_openai_evals |
| primary | B3 | T2 | — † | — | fab | — | https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/evaluation-dataset |
| primary | B3 | T2 | — † | — | fab | — | https://docs.evalsone.com/Faq/Samples/jsonl_file_format/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.rs/mur-common/latest/mur_common/eval/index.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/openai/evals/blob/main/docs/build-eval.md |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/openai/evals/blob/main/evals/registry/data/actors-sequence/samples.jsonl |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agentcontract/spec/blob/refs/heads/main/SPEC.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/weijen/agent-delivery-harness/blob/main/docs/evaluation/observability-and-trace-schema.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/jakyeamos/agent-eval-contract |
| primary | B3 | T2 | — † | — | kim | — | https://github.laiyagushi.com/b1rdmania/agent-kit |
| primary | B3 | T2 | — † | — | cur | — | https://huggingface.co/blog/tegridydev/llm-dataset-formats-101-hugging-face |
| research | B2 | T3 | 2026 | exc | fab | — | https://futureagi.com/blog/what-is-llm-dataset-2026/ |
| research | B2 | T3 | 2026-06 | exc | cur | — | https://arxiv.org/pdf/2606.14516 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.09610 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.11163 |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.13808 |
| research | B2 | T3 | 2026-01 | url | fab | — | https://arxiv.org/pdf/2601.17717 |
| research | B2 | T3 | 2026-01 | exc | fab | — | https://openreview.net/pdf?id=buDwV7LUA7 |
| research | B3 | T3 | 2025-10 | url | fab | — | https://arxiv.org/pdf/2510.23990 |
| research | B3 | T3 | 2025-06 | url | fab | — | https://arxiv.org/pdf/2506.04907 |
| research | B3 | T3 | 2025-01 | url | fab | — | https://arxiv.org/pdf/2501.10868 |
| research | B3 | T3 | 2024-07 | url | fab | — | https://arxiv.org/pdf/2407.03286 |
| research | B3 | T3 | — † | — | cur | — | https://github.com/evaleval/every_eval_ever/blob/main/README.md |
| research | B3 | T3 | — † | — | cur | — | https://huggingface.co/blog/Neo111x/integrating-benchmarks-into-lm-evaluation-harness |
| WILD | B2 | U | 2026 | exc | fab | — | https://chiraghasija.cc/posts/eval-driven-development-llm-apps-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://datanorth.ai/blog/evals-openais-framework-for-evaluating-llms |

### 6.2.3

**Q:** Human feedback capture path from UI (1.1) to store; is rater provenance (identity, task context) retained, and is feedback quality-checked before it feeds analysis (7.1) or any training signal?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.databricks.com/gcp/en/mlflow3/genai/human-feedback/expert-feedback/label-existing-traces |
| primary | B3 | T2 | — † | — | kim | — | https://docs.databricks.com/aws/en/mlflow3/genai/getting-started/human-feedback |
| primary | B3 | T2 | — † | — | kim | — | https://rlhf-annotation-studio.vercel.app/ |
| research | B1 | T3 | 2026-09 | url | fab | — | https://arxiv.org/html/2609.02859 |
| research | B2 | T3 | 2026 | exc | fab | — | https://futureagi.com/blog/integrating-user-feedback-automated-data-layers/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.29920 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.02255 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.25440 |
| research | B2 | T3 | 2026-05-04 | url | kim | — | https://tianpan.co/blog/2026/05/04/feedback-signal-provenance-ai-improvement-loops |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.22585 |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/html/2509.16779 |
| research | B3 | T3 | 2024-08 | url | fab | — | https://arxiv.org/pdf/2408.08411 |
| research | B3 | T3 | 2024-04 | url | fab | — | https://arxiv.org/pdf/2404.08555 |
| research | B3 | T3 | 2023-10 | url | fab | — | https://arxiv.org/pdf/2310.12773 |
| research | B3 | T3 | 2023-05 | url | fab | — | https://arxiv.org/pdf/2305.12894 |
| research | B3 | T3 | 2023-03 | url | fab | — | https://arxiv.org/pdf/2303.18223 |
| research | B3 | T3 | — † | — | fab | — | https://www.annotera.ai/blog/rlhf-human-annotation-guide/ |
| research | B3 | T3 | — † | — | fab | — | https://latitude.so/blog/human-feedback-llm-validation-workflows |
| research | B3 | T3 | — † | — | kim | — | https://nhimg.org/faq/why-do-ai-feedback-loops-need-provenance-and-versioning/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.confident-ai.com/knowledge-base/compare/best-ai-quality-platforms-for-human-annotation |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.herohunt.ai/blog/how-to-assess-human-data-labelers-screening-the-ai-workforce-guide/ |

### 6.3.1

**Q:** OpenLineage as the contract? Entity model: run, prompt, model, dataset, tool version, artifact.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur fab kim | — | https://github.com/OpenLineage/OpenLineage/blob/main/spec/OpenLineage.md |
| core | B3 | T1 | — † | — | fab kim | 6.3.2 | https://github.com/OpenLineage/OpenLineage/blob/main/README.md |
| core | B3 | T1 | — † | — | kim | 6.3.3 | https://github.com/OpenLineage/OpenLineage/discussions/4407 |
| core | B3 | T1 | — † | — | kim | — | https://github.com/OpenLineage/OpenLineage/issues/4484 |
| core | B3 | T1 | — † | — | cur gpt | — | https://openlineage.io/docs/spec/object-model/ |
| core | B3 | T1 | — † | — | cur kim | — | https://openlineage.io/docs/spec/facets/ |
| core | B3 | T1 | — † | — | fab kim | 6.3.2 8.4.4 | https://openlineage.io/docs/ |
| core | B3 | T1 | — † | — | cur | — | https://openlineage.io/blog/extending-with-facets/ |
| primary | B1 | T2 | 2026-09-03 | exc | fab | — | https://docs.snowflake.com/en/release-notes/2026/other/2026-09-03-external-lineage-ga |
| primary | B2 | T2 | 2026-05-12 | exc | fab | — | https://pypi.org/project/openlineage-python/ |
| primary | B3 | T2 | — † | — | fab | — | https://airflow.apache.org/docs/apache-airflow-providers-openlineage/stable/commits.html |
| primary | B3 | T2 | — † | — | fab gpt | 6.3.2 | https://github.com/OpenLineage/OpenLineage |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/OpenLineage/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/open-aigp/aigp/blob/main/integrations/openlineage/semantic-conventions.md |
| primary | B3 | T2 | — † | — | fab | — | https://pypi.org/project/apache-airflow-providers-openlineage/ |
| research | B3 | T3 | — † | — | cur | — | https://www.bearingnode.com/post/aigov-aio11y-part-3-building-track-3 |
| research | B3 | T3 | — † | — | fab | 6.3.3 | https://www.ibm.com/new/announcements/openlineage-for-a-unified-lineage-view-across-structured-and-unstructured-data-to-enable-explainable-ai |
| WILD | B2 | U | 2026-05 | exc | fab | 6.3.5 | https://medium.com/@Shamimw/openlineage-the-open-standard-for-data-lineage-77e67a5f0488 |
| WILD | B3 | U | — † | — | fab | 6.3.5 | https://apxml.com/courses/data-governance-quality-observability-production/chapter-4-data-lineage-metadata-management/openlineage-standard |
| WILD | B3 | U | — † | — | fab | 6.3.4 | https://blog.bytedoodle.com/data-lineage-through-openlineage-events/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Codex_(AI_agent) |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/OpenAI_Operator |
| WILD | B3 | U | — † | — | fab | — | https://github.com/skcc00000app08542/OpenLineage |
| WILD | B3 | U | — † | — | fab | — | https://index.scala-lang.org/openlineage/openlineage |

### 6.3.2

**Q:** Overlap with provenance (5.2): one graph or two, and which is authoritative?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur fab | 6.3.4 | https://datahub.com/blog/open-source-data-lineage/ |
| research | B2 | T3 | 2026 | exc | fab | — | https://datahub.com/blog/data-lineage-tools/ |
| research | B2 | T3 | 2026-05-24 | url | cur kim | 6.3.4 | https://iceberglakehouse.com/posts/2026-05-24-openlineage-observability/ |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.06241 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.14283 |
| research | B3 | T3 | 2025-07 | url | fab | — | https://arxiv.org/pdf/2507.01075 |
| research | B3 | T3 | — † | — | fab | — | https://dl.acm.org/doi/10.1145/2452376.2452478 |
| research | B3 | T3 | — † | — | fab | — | https://doi.org/10.3390/ijgi10030139 |
| research | B3 | T3 | — † | — | fab | — | https://fairplus.github.io/the-fair-cookbook/content/recipes/reusability/provenance.html |
| research | B3 | T3 | — † | — | fab | — | https://www.researchgate.net/publication/266369089_The_W3C_PROV_family_of_specifications_for_modelling_provenance_metadata |
| research | B3 | T3 | — † | — | cur | — | https://safeguard.sh/resources/blog/in-toto-attestation-formats-review |
| research | B3 | T3 | — † | — | fab | — | https://www.sciencedirect.com/science/article/pii/S0198971517300558 |
| research | B3 | T3 | — † | — | kim | — | https://usemakoto.dev/comparison/decision-guide.html |
| WILD | B2 | U | 2026 | exc | fab | 6.3.3 | https://www.ovaledge.com/blog/ai-powered-open-source-data-lineage-tools |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.puppygraph.com/learn/automated-data-lineage-tools |
| WILD | B3 | U | — † | — | fab | — | https://www.snowflake.com/en/data-governance/data-lineage/data-provenance/ |
| WILD | B3 | U | — † | — | fab | — | https://truescreen.io/articles/data-provenance-definition-source-authenticity/ |

### 6.3.3

**Q:** Are workspace contents (3.4) and memory contents (4.4) recorded as inputs?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://github.com/openlineage |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/uczltw6/trace-file-lineage |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ravi1395/agentrec |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/meredian-labs/lore |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/cursor/agent-trace |
| WILD | B1 | U | 2026-07 | exc | fab | 8.4.2 | https://medium.com/@dewasheesh.rana/graph-databases-and-data-lineage-in-modern-ai-systems-from-first-principles-to-production-ready-d3e9bcf2fa5c |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/data-lineage/ |

### 6.3.4

**Q:** Lineage store (Marquez or other); query API.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-01-26 | url | fab | — | https://lfaidata.foundation/communityblog/2026/01/26/budgets-as-code-with-flyte-openlineage-and-marquez/ |
| core | B3 | T1 | — † | — | fab | — | https://openlineage.io/getting-started/ |
| primary | B3 | T2 | — † | — | fab | — | https://www.astronomer.io/docs/learn/marquez |
| primary | B3 | T2 | — † | — | fab | — | https://cratedb.com/docs/guide/integrate/marquez/index.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/MarquezProject/marquez/pull/3104 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/MarquezProject/marquez/blob/main/api/src/main/java/marquez/api/OpenLineageResource.java |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/MarquezProject/marquez |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/MTSWebServices/data-rentgen/tree/a6bb651feb5eaca6b686de58db9d276b4e579a79 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ilum-cloud/marquez/blob/main/README.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/MarquezProject/marquez/blob/main/spec/openapi.yml |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/marquezproject/marquez/blob/main/docs/docs/api/get-lineage-events.api.mdx |
| primary | B3 | T2 | — † | — | fab | — | https://marquezproject.ai/ |
| primary | B3 | T2 | — † | — | fab | — | https://marquezproject.ai/docs/category/metadata-api/ |
| primary | B3 | T2 | — † | — | fab | — | https://marquezproject.ai/docs/api/record-lineage/ |
| primary | B3 | T2 | — † | — | gpt | — | https://marquezproject.ai/docs/quickstart/ |
| primary | B3 | T2 | — † | — | cur | — | https://raw.githubusercontent.com/MarquezProject/marquez/0.40.0/spec/openapi.yml |
| research | B2 | T3 | 2026 | exc | fab | — | https://atlan.com/marquez-wework-open-source/ |
| research | B3 | T3 | — † | — | kim | — | https://datatrail.ai/blog/marquez-data-lineage-cost |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/amoussa-eduhub/datalineage-vs-openlineage-marquez-datahub-which-data-lineage-tool-should-you-use-2017 |
| research | B3 | T3 | — † | — | gpt | — | https://marquezproject.ai/blog/using-marquez-api/ |
| WILD | B2 | U | 2026-05-28 | exc | fab | — | https://dataengineeracademy.com/blog/openlineage-and-marquez-data-lineage-for-modern-pipelines/ |
| WILD | B3 | U | — † | — | fab | — | https://datatrail.ai/blog/airflow-data-lineage |
| WILD | B3 | U | — † | — | fab | — | https://github.com/erikalfthan/OpenLineage |
| WILD | B3 | U | — † | — | fab | — | https://ilya-bystrov.github.io/posts/dwh/lineage/marquez=.html |

### 6.3.5

**Q:** Can any completed job be reconstructed from lineage alone?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/OpenLineage/OpenLineage/blob/main/website/docs/spec/run-cycle.md |
| core | B3 | T1 | — † | — | cur | — | https://github.com/OpenLineage/OpenLineage/blob/58cea9a9dadc48b71bf25901778b31f829da1ace/spec/OpenLineage.md |
| core | B3 | T1 | — † | — | fab | — | https://github.com/OpenLineage/OpenLineage/blob/main/proposals/1837/static_lineage.md |
| core | B3 | T1 | — † | — | cur | — | https://openlineage.io/docs/spec/run-cycle/ |
| core | B3 | T1 | — † | — | cur | — | https://openlineage.io/blog/streaming-philosophy/ |
| research | B1 | T3 | 2026-09-08 | url | fab | 8.4.2 | https://oneuptime.com/blog/post/2026-09-08-lineage-root-cause-broken-dashboard/view |
| research | B1 | T3 | 2026-07 | url | kim | — | https://arxiv.org/html/2607.18816 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.22142 |
| research | B2 | T3 | 2026-05 | url | kim | — | https://arxiv.org/abs/2605.06365 |
| research | B3 | T3 | 2024-05 | url | fab | — | https://arxiv.org/pdf/2405.17701 |
| research | B3 | T3 | — † | — | kim | — | https://www.arxiv.org/pdf/2602.05353v2 |
| research | B3 | T3 | — † | — | kim | — | https://automatic.co/lineage |
| research | B3 | T3 | — † | — | fab | — | https://datahub.com/blog/data-lineage-for-ml/ |
| research | B3 | T3 | — † | — | fab | — | https://datahub.com/blog/data-lineage-vs-data-provenance/ |
| research | B3 | T3 | — † | — | kim | — | https://www.researchgate.net/publication/412821470_LEDGER_Claim-to-Evidence_Trace_Graphs_for_Auditing_LLM_Agents |
| WILD | B3 | U | — † | — | fab | — | https://agility-at-scale.com/ai/governance/model-lineage-and-reproducibility/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/feast-dev/feast/issues/5882 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11520801 |
| WILD | B3 | U | — † | — | fab | — | https://www.promptcloud.com/blog/data-lineage-and-provenance/ |
| WILD | B3 | U | — † | — | fab | — | https://www.zerve.ai/blog/data-lineage-vs-data-provenance |

## 7. Self-Improvement

### 7.1.1

**Q:** Inputs: 6.1–6.3 only? Output schema for findings / opportunities.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-15 | exc | cur | — | https://github.com/cogni-work/insight-wave/blob/main/cogni-portfolio/skills/trends-bridge/references/opportunity-schema.md |
| primary | B1 | T2 | 2026-07-20 | exc | cur | — | https://github.com/tachyon-beep/skillpacks/blob/main/plugins/axiom-system-archaeologist/skills/using-system-archaeologist/findings-schema.md |
| primary | B2 | T2 | 2026-05-10 | exc | cur | — | https://github.com/davidmatousek/tachi/blob/main/schemas/finding.yaml |
| primary | B2 | T2 | 2026-04-18 | exc | cur | — | https://github.com/amplitude/builder-skills/blob/221ffaa849a355ae11eec88630071c17020a4102/product-skills/skills/discover-opportunities/SKILL.md |
| primary | B3 | T2 | — † | — | kim | — | https://arize.com/ |
| primary | B3 | T2 | — † | — | kim | 7.1.3 | https://www.datadoghq.com/blog/from-traces-to-experiments-a-loop-for-improving-ai-agents/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agent-telemetry-spec/atsc/blob/main/SPEC.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agent-telemetry-spec/atsc |
| primary | B3 | T2 | — † | — | kim | — | https://www.langchain.com/blog/traces-start-agent-improvement-loop |
| research | B1 | T3 | 2026-06-12 | exc | cur | — | https://commonplace-projects.ghost.io/dr-2/ |
| research | B2 | T3 | 2026 | url | cur fab | 7.1.2 cursor:6.1.6 | https://www.braintrust.dev/articles/agent-observability-complete-guide-2026 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.29823 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.04990v1 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.04990 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/abs/2606.30560v1 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/abs/2606.30560 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.30560v1 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.29678 |
| WILD | B3 | U | — † | — | fab | 7.1.2 | https://arize.com/blog/best-ai-observability-tools-for-autonomous-agents-in-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/ai-agent-observability/ |
| WILD | B3 | U | — † | — | fab | 7.1.2 | https://www.confident-ai.com/knowledge-base/compare/best-ai-agent-observability-tools-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/ai-agent-observability-2026-tracing-monitoring-stack-guide |
| WILD | B3 | U | — † | — | fab | — | https://montecarlo.ai/blog-best-ai-observability-tools |
| WILD | B3 | U | — † | — | fab | — | https://montecarlo.ai/blog-agent-observability-tools |

### 7.1.2

**Q:** Is analysis itself a platform job (3.1)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-11 | exc | cur | — | https://mixpanel.com/blog/what-is-an-analytics-agent/ |
| primary | B1 | T2 | 2026-06-18 | exc | cur | — | https://answers.databricks.com/best-agentic-analytics-platforms |
| primary | B2 | T2 | 2026-05-14 | exc | cur | — | https://www.actian.com/ai-analyst/steward-agent/ |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/articles/top-llm-observability-tools-in-2026-a-pro-guide/ |
| research | B1 | T3 | 2026-07-28 | exc | cur | — | https://www.codestreaks.com/blog/analytics-agent-guide |
| research | B1 | T3 | 2026-07-04 | url | fab | — | https://lilianweng.github.io/posts/2026-07-04-harness/ |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/html/2605.27276v2 |
| research | B2 | T3 | 2026-03 | url | kim | — | https://ar5iv.labs.arxiv.org/html/2603.19461 |
| research | B3 | T3 | — † | — | kim | — | https://ai.meta.com/research/publications/hyperagents/ |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2606.27291 |
| research | B3 | T3 | — † | — | kim | — | https://powerdrill.ai/blog/self-improving-data-agents |
| research | B3 | T3 | — † | — | kim | — | https://vadim.blog/meta-optimizer-research-to-practice |
| WILD | B1 | U | 2026-07-05 | exc | cur | — | https://www.themuse.com/jobs/visa/applied-ai-engineer-agentic-analytics-platform |
| WILD | B3 | U | — † | — | fab | — | https://explainx.ai/blog/what-is-self-harness-ai-agents-complete-guide-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.getmaxim.ai/articles/top-5-tools-for-ai-agent-observability-in-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/leezythu/Awesome-Harness-Self-Improvement |
| WILD | B3 | U | — † | — | fab | — | https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering/blob/main/skills/self-improvement-loops/SKILL.md |
| WILD | B3 | U | — † | — | fab | — | https://levelop.dev/blog/ai-agent-orchestration-production-monitoring-tracing |
| WILD | B3 | U | — † | — | fab | — | https://o-mega.ai/articles/self-improving-ai-agents-the-2026-guide |
| WILD | B3 | U | — † | — | fab | — | https://openobserve.ai/llm-observability/ |
| WILD | B3 | U | — † | — | fab | — | https://shipwithai.io/blog/self-improving-agent-loop |

### 7.1.3

**Q:** Cadence and triggers; where findings are tracked.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-22 | exc | cur | — | https://github.com/thomas-powers-jr/cadence/blob/main/docs/reference/config.md |
| primary | B1 | T2 | 2026-08-20 | exc | cur | — | https://github.com/thomas-powers-jr/cadence/blob/main/docs/reference/commands.md |
| primary | B1 | T2 | 2026-08-10 | exc | cur | — | https://github.com/thomas-powers-jr/cadence/commit/85fc5d25d15670d3b580c5c4971e7585c1b3592f |
| primary | B2 | T2 | 2026-04-12 | exc | cur | — | https://developer.salesforce.com/docs/sales/sales-engagement/guide/sales-cadence-objects.html |
| primary | B2 | T2 | 2026-02-15 | exc | cur | — | https://github.com/manehorizons/cadence/blob/main/docs/reference/commands.md |
| primary | B3 | T2 | — † | — | kim | — | https://www.braintrust.dev/blog/active-observability-loop-patterns-debugger |
| primary | B3 | T2 | — † | — | kim | — | https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.19386 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.18173 |
| research | B3 | T3 | 2025-04 | url | fab | — | https://arxiv.org/pdf/2504.18985 |
| research | B3 | T3 | 2025-04 | url | fab | — | https://arxiv.org/html/2504.18985v1 |
| research | B3 | T3 | — † | — | fab | — | https://www.adaline.ai/blog/complete-guide-llm-ai-agent-evaluation-2026 |
| research | B3 | T3 | — † | — | kim | — | https://agentpatterns.ai/workflows/continuous-agent-improvement/ |
| research | B3 | T3 | — † | — | kim | — | https://www.augmentcode.com/guides/agent-learning-flywheel |
| research | B3 | T3 | — † | — | fab | — | https://dl.acm.org/doi/10.1145/3756681.3756946 |
| research | B3 | T3 | — † | — | fab | — | https://futureagi.com/blog/evaluate-google-adk-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://www.augmentcode.com/tools/best-ai-agent-evaluation-tools |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/ai-agent-evaluation-pipeline-2026-testing-methodology |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/agentic-ai-q3-2026-quarterly-outlook-12-scenarios-data |
| WILD | B3 | U | — † | — | fab | — | https://logiciel.io/blog/llm-eval-harness-internal-build-2026 |

### 7.2.1

**Q:** Experiment definition: what can vary (prompt, model, tool, workflow, policy)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-18 | exc | cur | — | https://elevenlabs.io/docs/eleven-agents/operate/experiments.mdx |
| primary | B1 | T2 | 2026-06-30 | exc | cur | — | https://github.github.com/gh-aw/experimental/experiments/ |
| primary | B2 | T2 | 2026 | url | fab | 7.4.1 | https://www.braintrust.dev/articles/best-prompt-versioning-tools-2025 |
| primary | B2 | T2 | 2026 | url | fab | 7.2.3 | https://mlflow.org/articles/types-of-ai-experiment-tracking-tools-2026-guide/ |
| primary | B2 | T2 | 2026 | url | fab | 7.4.1 | https://mlflow.org/articles/top-llm-prompt-versioning-platforms-3/ |
| primary | B2 | T2 | 2026-04-05 | exc | cur | — | https://learn.microsoft.com/en-us/agent-framework/agents/skills |
| research | B1 | T3 | 2026-07-22 | exc | cur | — | https://www.confident-ai.com/blog/llm-experimentation |
| research | B2 | T3 | 2026 | url | fab kim | 8.1.7 | https://arize.com/blog/top-5-ai-prompt-management-tools-for-2026/ |
| research | B2 | T3 | 2026-05-11 | exc | cur kim | — | https://www.growthbook.io/insights/run-experiments-ai-agents-workflows |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2605.17746v1 |
| research | B3 | T3 | — † | — | fab | — | https://futureagi.com/blog/optimizing-llm-experimentation-best-practices/ |
| research | B3 | T3 | — † | — | fab | — | https://futureagi.com/blog/what-is-llm-experimentation-2026/ |
| research | B3 | T3 | — † | — | fab | — | https://futureagi.com/blog/ai-prompting-llm-2025/ |
| research | B3 | T3 | — † | — | fab | — | https://www.getmaxim.ai/articles/a-practitioners-guide-to-prompt-engineering-in-2025/ |
| research | B3 | T3 | — † | — | fab | — | https://www.getmaxim.ai/articles/explore-how-ai-prompt-experimentation-can-unlock-effective-scalable-prompt-management/ |
| research | B3 | T3 | — † | — | kim | — | https://github.com/vasilyevdm/ai-agent-handbook/blob/HEAD/COMPREHENSIVE_AGENT_ENGINEERING_GUIDE_2026.md |
| research | B3 | T3 | — † | — | kim | — | https://www.inflectra.com/Ideas/Topic/AI-Agent-Prompt-Engineering.aspx |
| WILD | B2 | U | 2026 | url | fab | 7.4.1 | https://www.confident-ai.com/knowledge-base/compare/best-ai-evaluation-tools-for-prompt-experimentation-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.confident-ai.com/knowledge-base/compare/best-ai-prompt-management-tools-with-llm-observability-2026 |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/glossary/experiments/ |
| WILD | B3 | U | — † | — | fab | — | https://www.morphllm.com/llm-workflows |
| WILD | B3 | U | — † | — | fab | — | https://www.promptlayer.com/blog/best-prompt-management-tools-2026-field-guide/ |

### 7.2.2

**Q:** Isolation: separate namespace/tenant using the same contracts as production?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-25 | exc | cur | — | https://docs.temporal.io/evaluate/nexus |
| primary | B1 | T2 | 2026-07-14 | exc | cur | — | https://temporal.io/blog/announcing-nexus-connect-temporal-applications-across-isolated-namespaces |
| primary | B3 | T2 | 2025-11-10 | exc | cur | — | https://cloud.google.com/kubernetes-engine/docs/concepts/multitenancy-overview |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/bruchansky/agent-policy-pipeline |
| research | B2 | T3 | 2026-03-31 | url | cur | — | https://oneuptime.com/blog/post/2026-03-31-dapr-multi-tenancy-namespaces/view |
| research | B2 | T3 | 2026-03-05 | url | fab | — | https://next.redhat.com/2026/03/05/zero-trust-ai-agents-on-kubernetes-what-i-learned-deploying-multi-agent-systems-on-kagenti/ |
| research | B2 | T3 | 2026-02-17 | url | cur | — | https://oneuptime.com/blog/post/2026-02-17-how-to-implement-namespace-per-tenant-isolation-on-gke-for-saas-applications/view |
| research | B3 | T3 | — † | — | kim | — | https://getautonoma.com/blog/ephemeral-environments |
| research | B3 | T3 | — † | — | fab | — | https://northflank.com/blog/sandboxes-on-kubernetes |
| research | B3 | T3 | — † | — | kim | — | https://northflank.com/blog/what-are-ephemeral-environments |
| research | B3 | T3 | — † | — | fab | — | https://www.signadot.com/blog/scaling-coding-agents-enterprise-kubernetes/ |
| research | B3 | T3 | — † | — | kim | — | https://thenewstack.io/new-tenant-is-change/ |
| research | B3 | T3 | — † | — | fab | 10.1.6 | https://truto.one/blog/how-to-architect-strict-data-isolation-in-multi-tenant-rag-pipelines/ |
| research | B3 | T3 | — † | — | fab | — | https://www.vcluster.com/blog/why-a-tenancy-layer-belongs-in-the-kubernetes-tech-stack-in-2026 |
| WILD | B3 | U | — † | — | fab | — | https://cloudnativenow.com/contributed-content/the-new-multi-tenant-challenge-securing-ai-agents-in-cloud-native-infrastructure/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8706772 |
| WILD | B3 | U | — † | — | fab | — | https://lucaberton.com/blog/kubecon-japan-2026-security-isolation-sovereign-ai/ |
| WILD | B3 | U | — † | — | fab | — | https://rajinikanthvadla.com/blog/kubernetes-cloud-native-ai-ml-deployment-trends-2026-moicyegk/ |

### 7.2.3

**Q:** Experiment tracking tool (no standard; MLflow-style) behind a port.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-30 | exc | cur | — | https://github.com/gradio-app/trackio |
| primary | B1 | T2 | 2026-08-01 | exc | cur | — | https://pypi.org/project/exptrack/ |
| primary | B1 | T2 | 2026-07-15 | exc | cur | — | https://pypi.org/project/extract-tracker/ |
| primary | B2 | T2 | 2026 | url | fab | — | https://www.guvi.in/blog/mlflow-experiment-tracking/ |
| primary | B2 | T2 | 2026 | url | fab | — | https://mlflow.org/ |
| primary | B2 | T2 | 2026-06-08 | exc | cur | — | https://pypi.org/project/expctl/ |
| primary | B2 | T2 | 2026-04-20 | exc | cur | — | https://pypi.org/project/koobi/ |
| primary | B2 | T2 | 2026-03-05 | exc | gpt | — | https://github.com/mlflow/mlflow/blob/master/CHANGELOG.md |
| primary | B2 | T2 | 2026-03-05 | exc | gpt | — | https://mlflow.org/releases/3.10.1/ |
| primary | B3 | T2 | — † | — | kim | — | https://adk.dev/integrations/mlflow-tracing/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.databricks.com/aws/en/mlflow/tracking |
| primary | B3 | T2 | — † | — | fab | — | https://docs.databricks.com/aws/en/mlflow/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/gorevds/litemlflow |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/desek/agent-observability |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/gorevds/litemlflow/blob/master/docs/vision.md |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/docs/latest/genai/eval-monitor/ |
| primary | B3 | T2 | — † | — | kim | — | https://mlflow.org/docs/latest/genai/tracing/opentelemetry/ingest/ |
| primary | B3 | T2 | — † | — | gpt | — | https://www.mlflow.org/releases/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2606.11045 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2505.23723 |
| WILD | B3 | U | — † | — | fab | — | https://letsdatascience.com/blog/mlflow-experiment-tracking-and-ml-lifecycle-management |

### 7.2.4

**Q:** Randomization and traffic-split mechanism.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-16 | exc | cur | — | https://docs.together.ai/docs/dedicated-endpoints/route-traffic |
| primary | B1 | T2 | 2026-07-09 | exc | cur | — | https://docs.datadoghq.com/feature_flags/concepts/traffic_splitting.md |
| primary | B2 | T2 | 2026-03-12 | exc | cur | — | https://doc.traefik.io/traefik-hub/api-gateway/expose/services/api-gateway-load-balancing |
| primary | B3 | T2 | 2025-10-15 | exc | cur | — | https://cloud.google.com/appengine/docs/standard/splitting-traffic |
| primary | B3 | T2 | — † | — | kim | — | https://docs.ensemble.ai/conductor/core-concepts/ab-testing |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/david-spies/context-ring |
| research | B1 | T3 | 2026-06-25 | exc | cur | — | https://github.com/jesselpalmer/traffic-splitter |
| research | B2 | T3 | 2026 | url | fab | — | https://inspectlet.com/guides/ab-testing |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/1508.07678 |
| research | B3 | T3 | — † | — | kim | — | https://atlan.com/know/ab-testing-llm-applications/ |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/how-to-ab-test-an-ai-agent.html |
| research | B3 | T3 | — † | — | kim | — | https://www.growthbook.io/insights/ab-testing-llms |
| WILD | B2 | U | 2026-02-17 | age | fab | — | https://oneuptime.com/blog/post/2026-02-17-how-to-set-up-traffic-splitting-in-app-engine-for-ab-testing-between-service-versions/view |
| WILD | B3 | U | — † | — | fab | — | https://docs.uniform.app/docs/knowledge-base/ensuring-accurate-traffic-splits-in-ab-testing |
| WILD | B3 | U | — † | — | fab | — | https://www.dynamicyield.com/lesson/traffic-allocation/ |
| WILD | B3 | U | — † | — | fab | — | https://guessthetest.com/unequal-allocation-of-traffic-in-a-b-tests-pros-and-cons/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@nktn.lx/a-b-testing-exploring-traffic-splitting-techniques-with-code-snippets-3cce9b06c2e5 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/marvelous-mlops/traffic-splits-arent-true-a-b-testing-for-machine-learning-models-62f77d10c993 |
| WILD | B3 | U | — † | — | fab | — | https://www.optimizely.com/optimization-glossary/ab-testing |
| WILD | B3 | U | — † | — | fab | — | https://support.crazyegg.com/hc/en-us/articles/28136405023635-Crazy-Egg-A-B-Tests-Guide-to-Classic-Split-Testing |

### 7.2.5

**Q:** Data-use basis: a flag carried from intake (2.1) that governs whether a job's inputs and outputs may be used in experiments (7.2) or fed into knowledge (8.3), independent of classification (10.5.1)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2374 |
| primary | B3 | T2 | — † | — | kim | — | https://llmconsent.org/ |
| primary | B3 | T2 | — † | — | kim | — | https://openai.com/index/offering-zero-data-retention-for-frontier-models/ |
| primary | B3 | T2 | — † | — | kim | — | https://rcan.dev/docs/training-consent/ |
| research | B3 | T3 | — † | — | fab | — | https://www.harness.io/blog/canary-release-feature-flags |
| research | B3 | T3 | — † | — | kim | — | https://stealthcloud.ai/ai-privacy/ai-training-consent-architecture/ |
| WILD | B2 | U | 2026 | url | fab | — | https://loadfocus.com/blog/2025/10/canary-deployment |
| WILD | B2 | U | 2026-02 | age | fab | — | https://medium.com/@ss-tech/you-absolutely-can-have-canary-releases-without-using-feature-flags-37bd4b6faa21 |
| WILD | B3 | U | — † | — | fab | — | https://chaordic.io/blog/feature-flagging-a-b-testing-canary-releases-explained |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@priyansu011/progressive-delivery-canary-deployments-feature-flags-a-b-testing-320d1337b3ce |
| WILD | B3 | U | — † | — | fab | — | https://www.meerako.com/blogs/feature-flags-guide-canary-release-ab-testing-launchdarkly |
| WILD | B3 | U | — † | — | fab | — | https://posthog.com/tutorials/canary-release |
| WILD | B3 | U | — † | — | fab | — | https://stonetusker.com/implementing-canary-deployments-with-feature-flags-in-ci-cd-pipelines/ |
| WILD | B3 | U | — † | — | fab | — | https://www.wissen.com/blog/the-role-of-blue-green-canary-and-feature-flags |

### 7.3.1

**Q:** Holdout governance: who can read; leakage prevention from memory (4.4).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-20 | exc | cur kim | 8.3.4 | https://github.com/OneNomad-LLC/przm-bench/blob/main/fixtures/HOLDOUT_PROTOCOL.md |
| primary | B2 | T2 | 2026-02-14 | exc | cur | — | https://docs.rs/crate/holdout/latest/source/launch/writeup.md |
| primary | B3 | T2 | — † | — | kim | — | https://evalguard.ai/docs/blueprints/governed-memory-agent |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/jmagly/aiwg/blob/main/agentic/code/frameworks/sdlc-complete/rules/reproducibility.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/hexo-ai/sia/pull/36 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/AgentEvalHQ/AgentEval/blob/main/docs/gatekeeper/memory-security.md |
| research | B1 | T3 | 2026-07-11 | exc | cur | — | https://ai-rng.com/training-time-evaluation-harnesses-and-holdout-discipline/ |
| research | B2 | T3 | 2026 | url | fab | — | https://layerxsecurity.com/generative-ai/best-ai-data-leakage-prevention-tools/ |
| research | B2 | T3 | 2026-05-18 | exc | cur | — | https://dataopsschool.com/blog/holdout-set/ |
| research | B2 | T3 | 2026-04-02 | exc | cur | — | https://theneuralbase.com/llm-benchmarks/learn/advanced/holdout-verification/ |
| research | B2 | T3 | 2026-03 | url | fab | 8.3.4 | https://arxiv.org/pdf/2603.16642 |
| research | B3 | T3 | — † | — | fab | — | https://accuknox.com/blog/ai-security-and-governance-guide |
| research | B3 | T3 | — † | — | kim | — | https://ai-rng.com/leakage-prevention-for-evaluation-datasets/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2505.00612 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2508.14706 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2511.18649 |
| research | B3 | T3 | — † | — | fab | 8.3.4 | https://www.statsig.com/perspectives/preventingdataleakage |
| WILD | B3 | U | — † | — | fab | — | https://www.venn.com/learn/dlp/data-leakage/ |

### 7.3.2

**Q:** Same validator port as 5.1?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-17 | exc | cur | — | https://github.com/Codagent-AI/agent-validator |
| primary | B1 | T2 | 2026-08-12 | exc | cur | — | https://github.com/codagent-ai/agent-validator/blob/main/docs/config-reference.md |
| primary | B1 | T2 | 2026-08-05 | exc | cur | — | https://github.com/codagent-ai/agent-validator/blob/main/docs/setup.md |
| primary | B1 | T2 | 2026-07-28 | exc | cur | — | https://github.com/Codagent-AI/agent-validator/blob/main/README.md |
| primary | B2 | T2 | 2026-03-22 | exc | cur | — | https://docs.agent-vault.dev/self-hosting/environment-variables |
| primary | B3 | T2 | — † | — | kim | — | https://docs.spring.io/spring-framework/reference/core/validation/validator.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/proflandrigan/emergent-flow/pull/147 |
| primary | B3 | T2 | — † | — | kim | — | https://jakarta.ee/specifications/platform/9/apidocs/jakarta/validation/validator |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/vally/reference/experiment-file/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2512.10169 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2507.21504v1 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/abs/2508.17393 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2604.19818 |
| research | B3 | T3 | — † | — | fab | — | https://www.getmaxim.ai/articles/a-comprehensive-guide-to-testing-and-evaluating-ai-agents-in-production/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.turingcollege.com/blog/evaluating-ai-agents-practical-guide |
| WILD | B3 | U | — † | — | fab | — | https://www.braintrust.dev/articles/top-5-platforms-for-agent-evals-in-2025 |
| WILD | B3 | U | — † | — | fab | — | https://fast.io/resources/best-tools-ai-agent-evaluation/ |

### 7.3.3

**Q:** Statistical acceptance criteria (minimum sample size / power, correction for multiple comparisons); regression suite required for every promotion.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-28 | exc | cur | — | https://github.com/tangle-network/agent-eval/blob/48fcaf8e/src/campaign/gates/heldout-gate.ts |
| primary | B1 | T2 | 2026-08-25 | exc | cur | 10.6.6 | https://github.com/tangle-network/agent-eval/blob/48fcaf8e/src/campaign/gates/default-production-gate.ts |
| primary | B1 | T2 | 2026-06-15 | exc | cur | — | https://github.com/tangle-network/agent-runtime/blob/cc4dc3f3/src/runtime/promotion-gate.ts |
| primary | B3 | T2 | — † | — | fab | — | https://developer.harness.io/docs/feature-management-experimentation/experimentation/key-concepts/multiple-comparison-correction/ |
| research | B1 | T3 | 2026-08-10 | exc | cur | — | https://tangle.tools/blog/self-improving-stack-evaluation-gates/ |
| research | B1 | T3 | 2026-07-04 | exc | cur | 10.6.6 | https://deepwiki.com/tangle-network/agent-eval/3.3-promotion-gates-and-statistical-release |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2305.11921 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2502.19364 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/1909.01421 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2009.09993 |
| research | B3 | T3 | — † | — | kim | — | https://clawrxiv.io/abs/2604.01974 |
| research | B3 | T3 | — † | — | kim | — | https://doi.org/10.48550/arxiv.2602.07150 |
| research | B3 | T3 | — † | — | kim | — | https://latenteval.ai/research/how-many-runs-for-a-reliable-eval |
| research | B3 | T3 | — † | — | kim | — | https://latenteval.ai/research/agent-reliability-testing-checklist |
| research | B3 | T3 | — † | — | kim | — | https://latenteval.ai/research/agent-reliability-testing |
| research | B3 | T3 | — † | — | fab | — | https://www.sciencedirect.com/science/article/pii/S2590260123000115 |
| WILD | B3 | U | — † | — | fab | — | https://displayrdocs.zendesk.com/hc/en-us/articles/7945091190671-Multiple-Comparisons-Post-Hoc-Testing |
| WILD | B3 | U | — † | — | fab | — | https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10866323/ |
| WILD | B3 | U | — † | — | fab | — | https://www.statsig.com/glossary/correction-for-multiple-comparisons |

### 7.3.4

**Q:** LLM-as-judge calibration: is judge agreement with human raters measured and tracked, and does judge model or prompt drift trigger re-calibration before the judge is trusted for a promotion decision?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.llmtrace.io/runbooks/judge-golden-set-drift/ |
| research | B2 | T3 | 2026 | url | fab kim | — | https://futureagi.com/blog/llm-as-judge-best-practices-2026/ |
| research | B2 | T3 | 2026 | url | fab kim | — | https://galileo.ai/blog/calibrate-llm-judge-human-annotations |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2407.18370 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2606.08172 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2507.16075 |
| research | B3 | T3 | — † | — | kim | — | https://netflixtechblog.medium.com/the-lifecycle-of-llm-as-a-judge-building-aligning-and-monitoring-at-scale-c95bd8283508 |
| research | B3 | T3 | — † | — | kim | — | https://qaskills.sh/blog/llm-eval-judge-model-drift-detection |
| WILD | B2 | U | 2026 | url | fab | — | https://www.koji.so/docs/llm-as-a-judge-vs-human-evaluation |

### 7.3.5

**Q:** Public benchmarks: is a decontamination check referenced (provider model card, dataset-overlap report), or is only the platform-owned holdout (7.3.1) trusted for promotion?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://aclanthology.org/2026.gem-main.50/ |
| primary | B3 | T2 | — † | — | kim | — | http://github.laiyagushi.com/auraoneai/contamination-audit |
| research | B3 | T3 | 2024-06 | url | fab | 8.3.4 | https://arxiv.org/pdf/2406.13990 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2406.04244v1 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2605.21543 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2507.16812 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2509.00072 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2605.19999v1 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2509.25531 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2601.02907 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2407.21530 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2502.14425v2 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/html/2502.17521v2 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2510.26538 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2510.13888 |
| research | B3 | T3 | — † | — | kim | — | https://latenteval.ai/research/benchmark-contamination |
| research | B3 | T3 | — † | — | kim | — | https://mbrenndoerfer.com/writing/benchmark-contamination-llm-detection-mitigation |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/llm-benchmark-methodology-2026-contamination-leaderboard-guide |
| WILD | B3 | U | — † | — | fab | — | https://openreview.net/forum?id=wVDR2qmE28 |

### 7.4.1

**Q:** Promotion unit: a versioned bundle (prompts, tools, routing, playbooks, policy bundles from 2.2).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-29 | exc | cur | — | https://docs.mubit.ai/patterns/self-optimizing-prompts |
| primary | B1 | T2 | 2026-08-15 | exc | cur | — | https://github.com/aws/agentcore-cli/blob/main/docs/config-bundles.md |
| primary | B1 | T2 | 2026-06-10 | exc | cur | cursor:U.11 | https://docs.gloo.com/forge/architecture/agent-composition |
| primary | B2 | T2 | 2026 | url | fab | — | https://pydantic.dev/articles/best-prompt-management-tools |
| primary | B3 | T2 | — † | — | kim | — | https://gitcode.com/gh_mirrors/aut/autocontext/blob/main/docs/context-bundles.md |
| research | B1 | T3 | 2026-07-20 | exc | cur | — | https://builder.aws.com/content/3EqkWDxU11p5yzd9eHMTzgx9GDv/your-agents-arent-microservices-a-framework-for-peak-hour-deployments-of-agentic-systems |
| research | B2 | T3 | 2026-04-18 | exc | cur | — | https://github.com/leynos/podbot/blob/1a46d136/docs/adr-004-define-skill-bundle-and-prompt-ingestion-contracts.md |
| research | B3 | T3 | — † | — | kim | — | https://arize.com/blog/prompt-templates-as-configs-not-code/ |
| research | B3 | T3 | — † | — | kim | — | https://futureagi.com/blog/prompt-versioning-lifecycle-management-2026/ |
| research | B3 | T3 | — † | — | kim | — | https://playbook.agentskit.io/docs/pillars/ai-collaboration/prompt-versioning-pattern |
| research | B3 | T3 | — † | — | gpt | — | https://techarch.com.au/labs |
| WILD | B2 | U | 2026 | url | fab | 8.1.7 | https://www.buildmvpfast.com/blog/prompt-engineering-product-development-versioning-testing-2026 |
| WILD | B2 | U | 2026 | exc | fab | 8.1.7 | https://devtoollab.com/blog/best-prompt-management-tools |
| WILD | B2 | U | 2026 | url | fab | 8.1.7 10.2.5 | https://www.getmaxim.ai/articles/top-5-prompt-versioning-platforms-in-2026/ |
| WILD | B2 | U | 2026 | exc | fab | 8.1.7 10.2.5 | https://www.guideflow.com/blog/best-prompt-management-tools |

### 7.4.2

**Q:** Mechanism: GitOps commit → rollout; canary / percentage; rollback path.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | 2025-11-20 | exc | cur | — | https://argoproj.github.io/argo-rollouts/getting-started/ |
| primary | B3 | T2 | 2025-10-10 | exc | cur kim | — | https://argo-rollouts.readthedocs.io/en/stable/features/canary/ |
| primary | B3 | T2 | 2025-09-15 | exc | cur | — | https://argo-rollouts.readthedocs.io/en/stable/features/analysis/ |
| primary | B3 | T2 | 2025-08-01 | exc | cur | — | https://argo-rollouts.readthedocs.io/en/stable/FAQ |
| primary | B3 | T2 | — † | — | fab | — | https://akuity.io/blog/automating-blue-green-and-canary-deployments-with-argo-rollouts |
| primary | B3 | T2 | — † | — | kim | — | https://argoproj.github.io/argo-rollouts/features/specification/ |
| primary | B3 | T2 | — † | — | gpt | — | https://argoproj.github.io/argo-rollouts/features/rollback/ |
| primary | B3 | T2 | — † | — | kim | — | https://developer.harness.io/docs/continuous-delivery/gitops/argo-rollouts/argo-rollouts-with-cv/ |
| research | B2 | T3 | 2026-02-26 | age | cur fab | — | https://oneuptime.com/blog/post/2026-02-26-argocd-canary-deployments-argo-rollouts/view |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/cypher682/building-a-real-gitops-pipeline-argo-cd-canaries-cosign-keyless-signing-and-prometheus-gates-1o2i |
| research | B3 | T3 | — † | — | kim | — | https://devcheolu.com/en/posts/p8otIP2ohbCHYO77c1F3 |
| research | B3 | T3 | — † | — | fab | — | https://medium.com/@gobmj/automated-canary-deployment-with-rollback-in-kubernetes-cd43058bbf4e |
| research | B3 | T3 | — † | — | fab | — | https://octopus.com/devops/argo-rollouts/ |
| research | B3 | T3 | — † | — | fab | — | https://tetrate.io/blog/implementing-gitops-and-canary-deployment-with-argo-project-and-istio |
| WILD | B2 | U | 2026-02-09 | age | fab | — | https://oneuptime.com/blog/post/2026-02-09-canary-releases-flux-flagger-gitops/view |
| WILD | B3 | U | — † | — | fab | — | https://www.aviator.co/blog/automated-failover-and-git-rollback-strategies-with-gitops-and-argo-rollouts/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/canary-deployment?o=asc&s=stars |
| WILD | B3 | U | — † | — | fab | — | https://uplatz.com/blog/gitops-workflows-with-progressive-delivery-and-canary-deployments/ |

### 7.4.3

**Q:** Approval evidence and lineage link (6.3) to the experiment (7.2) that justified it.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | — | https://csrc.nist.gov/Events/2025/semiconductor-traceability-and-provenance-workshop |
| primary | B2 | T2 | 2026-06-09 | url | cur | — | https://github.com/nexus-substrate/nexus-agents/issues/3842 |
| primary | B3 | T2 | — † | — | fab kim | 8.5.4 | https://mlflow.org/articles/automating-ai-model-registry-updates/ |
| primary | B3 | T2 | — † | — | kim | 8.5.4 | https://mlflow.org/articles/role-of-shared-model-registry/ |
| research | B2 | T3 | 2026-06-05 | exc | cur | — | https://github.com/nexus-substrate/nexus-agents/blob/main/docs/adr/0017-authority-ladder.md |
| research | B2 | T3 | 2026-05-12 | exc | cur | — | https://github.com/agent-axiom/agent-arch/blob/main/docs/book/part-v/evidence-spine.en.md |
| research | B2 | T3 | 2026-04-14 | exc | cur | — | https://www.permit.io/blog/agent-audit-logs-causal-commit-log |
| research | B2 | T3 | 2026-01-20 | exc | cur kim | 10.2.5 | https://nhimg.org/faq/which-control-matters-most-when-ai-changes-need-to-be-audited/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2504.11278 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/1511.09059 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2312.11028 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/1511.09065 |
| research | B3 | T3 | — † | — | fab | — | https://www.elixirdata.co/product/decision-lineage/ |
| research | B3 | T3 | — † | — | kim | — | https://www.kriv.ai/articles/model-risk-management-on-databricks-mlflow-lineage-and-policy-controls |
| research | B3 | T3 | — † | — | kim | — | https://petronellatech.com/blog/evidence-first-cloud-governance-for-ai-analytics/ |
| research | B3 | T3 | — † | — | fab | — | https://pmc.ncbi.nlm.nih.gov/articles/PMC13526443/ |
| research | B3 | T3 | — † | — | kim | — | https://theneuralbase.com/mlflow/learn/advanced/automated-registry-promotion/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.getcollate.io/learning-center/data-lineage-regulatory-reporting |
| WILD | B2 | U | 2026 | url | fab | — | https://www.ovaledge.com/blog/data-lineage-best-practices |
| WILD | B3 | U | — † | — | fab | — | https://datahub.com/blog/data-lineage-for-compliance/ |
| WILD | B3 | U | — † | — | fab | — | https://kla.digital/tamper-proof-evidence |
| WILD | B3 | U | — † | — | fab | — | https://www.mdpi.com/2673-8244/5/3/52 |
| WILD | B3 | U | — † | — | fab | — | https://www.mdpi.com/2076-3417/15/11/6062 |
| WILD | B3 | U | — † | — | fab | — | https://www.scnsoft.com/blockchain/traceability-provenance |
| WILD | B3 | U | — † | — | fab | — | https://ucdbg.github.io/ProvenanceWeek2025/ |

### 7.4.4

**Q:** Post-promotion measurement: is production outcome (6.1, 6.2) after a promotion compared with the pre-promotion baseline and the experiment's (7.2) predicted effect, with automatic rollback (7.4.2) if the gain does not materialize?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://www.evidentlyai.com/ml-in-production/model-monitoring |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Emart29/ml-canary-deploy |
| primary | B3 | T2 | — † | — | fab | — | https://signoz.io/guides/model-monitoring/ |
| primary | B3 | T2 | — † | — | fab | — | https://witness.ai/blog/model-monitoring/ |
| research | B1 | T3 | 2026-09-01 | url | gpt | — | https://opcreport.github.io/2026/09/01/opc-report-2026-09-01-1603/ |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2503.16332 |
| research | B3 | T3 | — † | — | fab | — | https://arxiv.org/pdf/2501.10774 |
| research | B3 | T3 | — † | — | kim | — | https://johal.in/model-rollback-strategies-for-failed-ml-deployments |
| research | B3 | T3 | — † | — | kim | — | https://johal.in/implement-model-rollbacks-for-ml-on-kubernetes-with-flagger |
| research | B3 | T3 | — † | — | kim | — | https://mortalapps.com/agents/production-engineering/automated-rollbacks-for-agents/ |
| research | B3 | T3 | — † | — | fab | — | https://www.researchgate.net/publication/387022445_Model_Drift_Monitoring_Continuously_Tracking_Model_Performance_Metrics_to_Detect_Accuracy_Degradation |
| research | B3 | T3 | — † | — | kim | — | https://sysart.consulting/insights/automated-model-rollback-on-premises-ai/ |
| research | B3 | T3 | — † | — | fab | — | https://towardsdatascience.com/monitoring-machine-learning-models-in-production-why-and-how-13d07a5ff0c6/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.deepmarketing.it/en/blog/trade-promotion-roi-incrementality-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://sreschool.com/blog/baseline/ |
| WILD | B2 | U | 2026-01-30 | age | fab | — | https://oneuptime.com/blog/post/2026-01-30-automatic-rollback-triggers/view |
| WILD | B3 | U | — † | — | fab | — | https://www.bedrockanalytics.com/blog/how-promo-lift-is-measured-in-cpg |
| WILD | B3 | U | — † | — | fab | — | https://www.heavybit.com/library/article/machine-learning-model-monitoring |
| WILD | B3 | U | — † | — | fab | — | https://www.statsig.com/perspectives/model-performance-quality-decline |

## 8. Shared Platform Services (open source only)

### 8.1.1

**Q:** Git is the standard; forge API differences (GitHub / GitLab / Gitea) hidden behind a port?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.magit.vc/forge/How-Forge-Detection-Works.html |
| primary | B3 | T2 | — † | — | cur kim | — | https://docs.rs/vcs-forge/latest/vcs_forge/guide/index.html |
| primary | B3 | T2 | — † | — | cur | — | https://forge.go.phpboyscout.uk/explanation/backend-agnosticism/ |
| primary | B3 | T2 | — † | — | cur | — | https://forge.go.phpboyscout.uk/reference/providers/ |
| primary | B3 | T2 | — † | — | fab kim | — | https://git-pkgs.dev/docs/modules/forge/ |
| primary | B3 | T2 | — † | — | fab kim | — | https://github.com/git-pkgs/forge |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/getpaseo/paseo/issues/1616 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/Leleat/git-forge |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/yi-nology/git-platform-sdk |
| research | B2 | T3 | 2026-03-13 | url | cur | — | https://nesbitt.io/2026/03/13/forge.html |
| research | B3 | T3 | — † | — | kim | — | https://deepwiki.com/kenn-io/forge/3.1-platform-abstraction-layer |
| WILD | B2 | U | 2026 | url | fab | — | https://www.pkgpulse.com/guides/gitea-vs-forgejo-vs-gogs-self-hosted-git-platforms-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.serverspan.com/en/blog/the-2026-guide-to-self-hosted-git-gitea-forgejo-and-the-future-of-code-hosting |
| WILD | B2 | U | 2026-01 | url | fab | — | https://dasroot.net/posts/2026/01/self-hosted-git-platforms-gitlab-gitea-forgejo-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Gitea |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/GitLab |
| WILD | B3 | U | — † | — | fab | — | https://gitea.com/gitea/changelog |
| WILD | B3 | U | — † | — | fab | — | https://github.com/raylabshq/gitea-mirror |
| WILD | B3 | U | — † | — | fab | — | https://kx.cloudingenium.com/en/gitea-self-hosted-git-forge-github-alternative-guide/ |

### 8.1.2

**Q:** Worktree/branch per job (3.1) convention; cleanup policy.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-07-09 | exc | gpt | — | https://docs.rs/crate/ai-dispatch/10.39.0/source/CHANGELOG.md |
| primary | B2 | T2 | 2026-04-17 | exc | gpt | — | https://docs.rs/crate/ai-dispatch/10.17.1/source/CHANGELOG.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/enuno/claude-command-and-control/blob/main/commands-templates/orchestration/worktree-setup.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/timothyjrainwater-lab/multi-agent-coordination-framework/blob/main/patterns/WORKTREE_ISOLATION_PROTOCOL.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Ck1sap/borghei-Claude-Skills/blob/main/engineering/git-worktree-manager/SKILL.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/nanasess/git-worktree-manager |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/anthropics/claude-code/issues/74719 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/retif/stalewood |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/wycats/worktree-gc |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/scitex-ai/scitex-agent-container/pull/722 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ai-ecoverse/gh-reaper |
| research | B1 | T3 | 2026-08-19 | url | fab | — | https://compositecode.blog/2026/08/19/worktrees/ |
| research | B2 | T3 | 2026-04-01 | url | kim | — | https://blog.appxlab.io/2026/04/01/parallel-ai-coding-agents-git-worktrees/ |
| research | B3 | T3 | — † | — | kim | — | https://ctxwire.com/articles/git-worktrees-for-coding-agents/ |
| research | B3 | T3 | — † | — | fab kim | — | https://dev.to/andrea_schiona/running-coding-agents-in-parallel-with-git-worktrees-4cnk |
| research | B3 | T3 | — † | — | cur | — | https://medium.com/israeli-tech-radar/one-repo-many-hands-a-git-worktree-methodology-for-the-agentic-developer-832ceed64031 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.codeagentswarm.com/en/guides/git-worktree-vs-branch-parallel-ai-agents |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.developersdigest.tech/blog/git-worktrees-claude-code-parallel-agents-guide |
| WILD | B2 | U | 2026 | exc | fab | — | https://devtoollab.com/blog/claude-code-git-worktrees-parallel-agents-guide |
| WILD | B2 | U | 2026 | exc | fab | — | https://jonathansblog.co.uk/git-worktrees-vs-branches-a-complete-guide-for-developers-and-ai-coding-agents |
| WILD | B3 | U | — † | — | fab | — | https://arbitlab.com/blog/git-worktree-cleanup |
| WILD | B3 | U | — † | — | fab | — | https://www.augmentcode.com/guides/git-worktrees-parallel-ai-agent-execution |
| WILD | B3 | U | — † | — | fab | — | https://www.mindstudio.ai/blog/git-worktrees-parallel-ai-coding-agents |
| WILD | B3 | U | — † | — | fab | — | https://nimbalyst.com/blog/git-worktrees-for-ai-coding-agents-complete-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://www.termdock.com/en/blog/git-worktree-multi-agent-setup |

### 8.1.3

**Q:** AGENTS.md placement and precedence rules.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur fab kim | cursor:9.5.1 cursor:9.5.2 | https://agents.md/ |
| core | B3 | T1 | — † | — | cur gpt | cursor:9.5.1 cursor:9.5.2 cursor:9.5.4 | https://github.com/agentsmd/agents.md/issues/135 |
| primary | B1 | T2 | 2026-08 | age | cur kim | cursor:3.4.6 cursor:9.5.2 cursor:9.5.3 cursor:9.5.5 | https://developers.openai.com/codex/guides/agents-md |
| primary | B3 | T2 | — † | — | fab | — | https://docs.atlan.com/agents/concepts/agents-md |
| primary | B3 | T2 | — † | — | cur fab | cursor:9.5.1 | https://github.com/agentsmd/agents.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/openai/codex/blob/main/codex-rs/core/src/agents_md.rs |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/openai/codex/blob/d807d44a/codex-rs/core/src/project_doc.rs |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/openai/codex/issues/7138 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/openai/codex/blob/ac4332c05b11e00ae775a24cb762edc05c5b5932/codex-rs/core/src/agents_md.rs |
| research | B1 | T3 | 2026-07 | age | cur kim | cursor:3.4.6 | https://getknack.ai/blog/agents-md-monorepo |
| research | B2 | T3 | 2026 | exc | fab | — | https://www.tembo.io/blog/agents-md |
| research | B2 | T3 | 2026-05 | url | fab | — | https://www.iuriio.com/blog/posts/2026/05/agents-md-field-guide-2026 |
| research | B2 | T3 | 2026-03-26 | url | fab | — | https://codex.danielvaughan.com/2026/03/26/agents-md-advanced-patterns/ |
| research | B3 | T3 | — † | — | fab | — | https://blakecrosley.com/blog/agents-md-patterns |
| research | B3 | T3 | — † | — | kim | — | https://heycc.cn/en/posts/agents-md-open-standard-guide/ |
| research | B3 | T3 | — † | — | cur | — | https://inventivehq.com/blog/claude-md-vs-agents-md-vs-gemini-md |
| research | B3 | T3 | — † | — | kim | — | https://rohitghumare.com/blog/agents-md-best-practices/ |
| WILD | B1 | U | 2026-08-03 | exc | gpt | — | https://github.com/indisoluble/AGENTS-spec/blob/master/AGENTS.md |
| WILD | B2 | U | 2026 | url | fab | — | https://promptessor.com/blog/best-agentsmd-examples-for-codex-cursor-and-ai-coding-agents-in-2026 |
| WILD | B3 | U | — † | — | fab | — | https://addozhang.medium.com/agents-md-a-new-standard-for-unified-coding-agent-instructions-0635fc5cb759 |
| WILD | B3 | U | — † | — | fab | — | https://agentic-ai.readthedocs.io/en/latest/Standards/agents-md/ |
| WILD | B3 | U | — † | — | fab | — | https://www.aihero.dev/a-complete-guide-to-agents-md |
| WILD | B3 | U | — † | — | fab | — | https://asdlc.io/practices/agents-md-spec/ |
| WILD | B3 | U | — † | — | fab | — | https://www.augmentcode.com/guides/agents-md-vs-claude-md |
| WILD | B3 | U | — † | — | gpt | — | https://github.com/TechSpokes/agency-specifications-files-agents-md/blob/main/SPECIFICATION.md |
| WILD | B3 | U | — † | — | cur | — | https://www.verdent.ai/guides/codex-agents-md-explained |

### 8.1.4

**Q:** CI contract: what the platform requires from any CI (status, artifacts, logs); relationship to validation (5.1).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://agent-ci.com/ |
| primary | B3 | T2 | — † | — | cur | — | https://archives.docs.gitlab.com/18.0/administration/cicd/job_artifacts/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.gitlab.com/17.9/administration/cicd/job_logs/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.gitlab.com/ci/migration/github_actions/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.gitlab.com/ci/pipelines/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/marketplace/actions/gitlab-pipeline-trigger |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/firecow/gitlab-ci-local |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/digital-blueprint/gitlab-pipeline-trigger-action |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Velascat/CxRP |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kabudu/guarded-continuation-checker/blob/master/docs/ARTIFACT_SCHEMA_V4.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/foo-ogawa/agent-contracts/blob/main/docs/cli-reference.md |
| primary | B3 | T2 | — † | — | cur | — | https://gitlab.com/gitlab-org/gitlab/-/blob/a10ad67099962741102b440ea090bfb82ce70eb3/doc/administration/job_logs.md |
| primary | B3 | T2 | — † | — | kim | — | https://lakelogic.github.io/LakeLogic/contracts/schema_api.html |
| primary | B3 | T2 | — † | — | kim | — | https://www.npmjs.com/package/agent-contracts |
| research | B2 | T3 | 2026 | exc | fab | — | https://www.stepsecurity.io/blog/datadogs-devsecops-2026-report-validates-what-weve-been-building |
| research | B2 | T3 | 2026-03-12 | url | fab | — | https://developers.redhat.com/articles/2026/03/12/how-develop-agentic-workflows-ci-pipeline-cicaddy |
| research | B2 | T3 | 2025-12-21 | url | fab | — | https://oneuptime.com/blog/post/2025-12-21-artifacts-gitlab-ci/view |
| research | B3 | T3 | — † | — | cur | — | https://cloudaware.com/blog/devsecops-compliance/ |
| research | B3 | T3 | — † | — | cur fab | — | https://prefactor.tech/blog/audit-trails-in-ci-cd-best-practices-for-ai-agents |
| WILD | B1 | U | 2026-06-15 | url | fab | — | https://tech.hub.ms/security/roundups/weekly-security-roundup-2026-06-15 |
| WILD | B2 | U | 2026-03 | exc | fab | — | https://medium.com/@roman_fedyskyi/a-safer-ci-pattern-for-agentic-code-review-94a484b5e3c4 |
| WILD | B3 | U | — † | — | fab | — | https://www.augmentcode.com/guides/api-contract-testing-agent-authored-specs |
| WILD | B3 | U | — † | — | fab | — | https://www.bitslovers.com/gitlab-ci-artifacts/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/raju_dandigam/deterministic-agent-contracts-without-making-ci-brittle-3nmp |
| WILD | B3 | U | — † | — | fab | — | https://www.freecodecamp.org/news/how-to-debug-cicd-pipelines-handbook/ |

### 8.1.5

**Q:** Instruction-file names: when harnesses (3.1) expect different files (AGENTS.md, CLAUDE.md, SKILL.md, others), does the platform keep one canonical file and generate or symlink the rest, or require every harness to read AGENTS.md?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | gpt | — | https://code.claude.com/docs/en/memory |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/fialhosoft/agentlink |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/MigueMercedes/pragspec/pull/6 |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/buildermethods/agentcanon |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/osolmaz/claude-md-symlinker |
| primary | B3 | T2 | — † | — | gpt | — | https://gitlab.com/gitlab-org/gitlab/-/blob/8df5c04acc6b3a13e35caa755f0a20e0164f26e4/AGENTS.md |
| primary | B3 | T2 | — † | — | gpt | — | https://platform.claude.com/docs/en/managed-agents/skills |
| research | B2 | T3 | 2026 | exc | fab | — | https://blink.new/blog/agents-md-vs-claude-md |
| research | B2 | T3 | 2026-05-27 | url | fab | — | https://codex.danielvaughan.com/2026/05/27/agent-instruction-files-agents-md-claude-md-cross-tool-portability-codex-cli/ |
| research | B2 | T3 | 2026-03-16 | exc | gpt | — | https://www.termdock.com/blog/skill-md-vs-claude-md-vs-agents-md |
| research | B3 | T3 | — † | — | fab kim | — | https://agyn.io/blog/claude-md-agents-md-compatibility |
| research | B3 | T3 | — † | — | cur kim | cursor:9.5.3 cursor:9.5.5 | https://www.alexdunlop.com/writing/claude-md-vs-agents-md |
| research | B3 | T3 | — † | — | fab | — | https://www.deployhq.com/blog/ai-coding-config-files-guide |
| research | B3 | T3 | — † | — | fab kim | — | https://gist.github.com/yurukusa/d36197848911f025add142abefcde685 |
| research | B3 | T3 | — † | — | fab | — | https://www.humanlayer.dev/blog/writing-a-good-claude-md |
| research | B3 | T3 | — † | — | gpt | — | https://opensource.adobe.com/ai-repo-harness-guide/skills/harness-setup/references/claude/ |
| WILD | B2 | U | 2026 | url | fab | — | https://amitray.com/claude-md-vs-agents-md-memory-md-skills-md-context-md-guide-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://explainx.ai/blog/agent-markdown-files-complete-guide-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://yurukusa.github.io/cc-safe-setup/agents-md-vs-claude-md.html |
| WILD | B3 | U | — † | — | fab | — | https://aq.dev/guides/keep-agents-md-and-claude-md-in-sync/ |
| WILD | B3 | U | — † | — | fab | — | https://betterthanrandom.substack.com/p/industry-roundup-11 |
| WILD | B3 | U | — † | — | fab | — | https://claudeskills.info/skills/getsentry/skills/agents-md/ |
| WILD | B3 | U | — † | — | fab | — | https://cobusgreyling.substack.com/p/what-is-agentsmd |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/@vrppaul/semantic-code-mcp/blob/ec06c4ade73c3e57c79951b3d267ffd65d9d7c84/docs/decisions/002-agent-instruction-files.md |
| WILD | B3 | U | — † | — | gpt | — | https://marketplace.agentscli.com/items/stealth-engine-skills-agents-md-setup |
| WILD | B3 | U | — † | — | gpt | — | https://skillmd.com/skills/lucaspmarie-a11y/agents-md |
| WILD | B3 | U | — † | — | gpt | — | https://skillproof.dev/glossary/agents-md |
| WILD | B3 | U | — † | — | gpt | — | https://www.skills.sh/stealth-factory/skills/agents-md-setup |

### 8.1.6

**Q:** Merge gate: are agent, prompt, and tool changes checked by an automated eval at PR time — replay against traces (6.1, 6.3) or a golden dataset (6.2) — distinct from the blind promotion gate (7.3); where does it run and what is the pass threshold?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | 10.6.6 | https://aws.amazon.com/blogs/machine-learning/automated-agent-evaluation-with-amazon-bedrock-agentcore-and-github-actions/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/hidai25/eval-view |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/hoomanesteki/tracegym-ai-agent-evaluation |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/theo-ai-lab/plimsoll |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/vdeshmukh1697/tracecase |
| primary | B3 | T2 | — † | — | kim | — | https://langfuse.com/resources/engineering/golden-dataset-evaluation |
| primary | B3 | T2 | — † | — | fab | — | https://www.promptfoo.dev/docs/integrations/ci-cd/ |
| research | B2 | T3 | 2026-05-17 | url | fab | — | https://zylos.ai/en/research/2026-05-17-agent-native-cicd-deployment-patterns/ |
| research | B2 | T3 | 2026-05-01 | url | fab | — | https://tianpan.co/blog/2026-05-01-eval-as-pull-request-comment-not-a-job |
| research | B3 | T3 | — † | — | kim | — | https://www.arthur.ai/column/regression-test-datasets-ai-agents-production-failures |
| research | B3 | T3 | — † | — | fab | — | https://galtea.ai/blog/automated-llm-evaluation-building-a-ci-cd-quality-gate-that-actually-runs |
| research | B3 | T3 | — † | — | fab | — | https://langfuse.com/resources/engineering/llm-regression-testing |
| research | B3 | T3 | — † | — | kim | — | https://pondero.ai/enterprise/guides/ci-for-agents-eval-gating-2026/ |
| WILD | B1 | U | 2026-07 | exc | fab | — | https://medium.com/@alexrodriguesj/testing-llm-prompts-like-code-regression-evals-in-ci-cd-with-promptfoo-5242b4dcb9be |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/glossary/llm-regression-testing/ |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/ci-cd-llm-eval-github-actions-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/prompt-regression-testing-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://qaskills.sh/blog/eval-driven-development-llm-guide-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://tech-insider.org/how-to-build-llm-evaluation-pipeline-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.kinde.com/learn/ai-for-software-engineering/ai-devops/ci-cd-for-evals-running-prompt-and-agent-regression-tests-in-github-actions/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@meryemmsakinn/end-vibe-driven-development-testing-ai-agents-in-ci-pipelines-promptfoo-golden-traces-b9b222b23d72 |
| WILD | B3 | U | — † | — | fab | — | https://qaskills.sh/blog/golden-dataset-llm-evaluation-guide |

### 8.1.7

**Q:** Prompts as code: authored and reviewed as template files in source control (8.1) under the same PR process, with the registry (8.5) tracking only promoted versions — or does a separate prompt-management system own the source of truth?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.port.io/guides/all/ingest-prompts-skills-from-github-using-gitops/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.promptlayer.com/features/prompt-registry/overview |
| primary | B3 | T2 | — † | — | fab | — | https://learning.sap.com/courses/solve-your-business-problems-using-prompts-and-llms-in-sap-generative-ai-hub/managing-prompts-with-the-prompt-registry-and-templates |
| primary | B3 | T2 | — † | — | fab | — | https://pi.dev/docs/latest/prompt-templates |
| primary | B3 | T2 | — † | — | fab | — | https://www.promptlayer.com/prompt-management/ |
| research | B2 | T3 | 2026-03-28 | exc | gpt | — | https://gist.github.com/dipandhali2021/f4753824c87cbbc5ff3e94d2c9d3e54f |
| research | B3 | T3 | — † | — | kim | — | https://agenta.ai/blog/git-vs-prompt-management-tools |
| research | B3 | T3 | — † | — | kim | — | https://ai-tldr.dev/learn/prompt-engineering/prompt-iteration/what-is-prompt-management/ |
| research | B3 | T3 | — † | — | fab | — | https://langwatch.ai/blog/what-is-prompt-management-and-how-to-version-control-deploy-prompts-in-productions |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/prompt-registry |
| WILD | B2 | U | 2026 | url | fab | — | https://www.braintrust.dev/articles/best-prompt-management-tools-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.truefoundry.com/blog/prompt-management-tools |
| WILD | B3 | U | — † | — | fab | — | https://apxml.com/courses/prompt-engineering-llm-application-development/chapter-3-prompt-design-iteration-evaluation/version-control-for-prompts |
| WILD | B3 | U | — † | — | fab | — | https://www.josecasanova.com/prompts/for/git |
| WILD | B3 | U | — † | — | fab | — | https://pidocs.seepine.com/en/prompt-templates |

### 8.2.1

**Q:** S3-compatible object API as the port; OCI artifacts (ORAS) for models / prompts / bundles?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-10-06 | url | fab | — | https://www.cncf.io/blog/2025/10/06/announcing-oras-v1-3-0-elevating-artifact-and-registry-management-workflows/ |
| core | B3 | T1 | — † | — | cur kim | — | https://github.com/oras-project/artifacts-spec |
| core | B3 | T1 | — † | — | kim | — | https://github.com/opencontainers/distribution-spec/issues/573 |
| core | B3 | T1 | — † | — | cur | — | https://oci-playground.github.io/specs-latest/specs/distribution/v1.0.0/oci-distribution-spec.html |
| core | B3 | T1 | — † | — | cur kim | — | https://oras.land/docs/concepts/reftypes |
| core | B3 | T1 | — † | — | fab kim | — | https://oras.land/ |
| primary | B1 | T2 | 2026-09-01 | url | gpt | — | https://aistore.nvidia.com/blog/2026/09/01/mlperf-storage-v3 |
| primary | B1 | T2 | 2026-08-13 | url | fab | — | https://developers.cloudflare.com/changelog/post/2026-08-13-oci-object-storage-cloud-connector/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.oracle.com/en-us/iaas/releasenotes/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/oras-project/oras/releases |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/oras-project/community/blob/main/governance/RELEASE-PROCESS.md |
| primary | B3 | T2 | — † | — | kim | — | https://kitops.org/docs/modelkit/intro/ |
| primary | B3 | T2 | — † | — | cur fab | — | https://learn.microsoft.com/en-us/azure/container-registry/container-registry-manage-artifact |
| primary | B3 | T2 | — † | — | cur fab kim | 8.5.2 | https://oras.land/docs/ |
| primary | B3 | T2 | — † | — | fab | 8.2.2 | https://oras.land/docs/concepts/artifact/ |
| primary | B3 | T2 | — † | — | fab | — | https://oras.land/blog/oras-new-release/ |
| research | B2 | T3 | 2026-03-03 | url | fab kim | — | https://blogs.vmware.com/cloud-foundation/2026/03/03/using-harbor-as-an-ai-model-registry/ |
| research | B3 | T3 | — † | — | fab | — | https://www.vcluster.com/blog/leveraging-generic-artifact-stores-with-oci-images-and-oras |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Orthanc_(server) |
| WILD | B3 | U | — † | — | fab | — | https://zenn.dev/zenogawa/articles/oras_oci_artifact?locale=en |

### 8.2.2

**Q:** Content addressing and immutability.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/crate/segstore/latest/source/docs/segstore-durability-sidecars.md |
| primary | B3 | T2 | — † | — | cur | — | https://epicgames.github.io/lore/explanation/system-design/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/epicgames/lore/blob/main/docs/explanation/system-design.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/arclabs561/segstore |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/artifact-depot/artifact-depot |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mochilang/mochi/blob/main/website/docs/research/0057/08-content-addressed-store.md |
| primary | B3 | T2 | — † | — | kim | — | https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/artifact_registry/decisions/008_content_addressable_storage/ |
| primary | B3 | T2 | — † | — | kim | — | https://handbook.gitlab.com/handbook/engineering/architecture/design-documents/artifact_registry/decisions/002_storage_deduplication_scope/ |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.06868 |
| research | B2 | T3 | 2026-02-18 | url | fab | — | https://nesbitt.io/2026/02/18/what-package-registries-could-borrow-from-oci.html |
| research | B2 | T3 | 2026-02-07 | url | fab | — | https://www.plakar.io/posts/2026-02-07/storing-backups-in-an-oci-registry/ |
| research | B3 | T3 | 2025-08 | url | fab | 8.5.5 | https://arxiv.org/pdf/2508.03095 |
| research | B3 | T3 | — † | — | fab | — | https://beyond.minimumcd.org/docs/migrate-to-cd/pipeline/immutable-artifacts/ |
| research | B3 | T3 | — † | — | fab | — | https://www.bretfisher.com/blog/oci-artifacts |
| research | B3 | T3 | — † | — | fab | — | https://www.docker.com/blog/oci-artifacts-for-ai-model-packaging/ |
| research | B3 | T3 | — † | — | gpt | — | https://docs.openlithohub.com/rfcs/0007-qdm-continuous-process-window-verification/ |
| research | B3 | T3 | — † | — | fab | — | https://research.versioneer.at/oras-101 |
| research | B3 | T3 | — † | — | kim | — | https://stonefly.com/blog/content-addressable-storage-enterprise-guide/ |
| research | B3 | T3 | — † | — | cur | — | https://t34ch.tech/articles/content-addressed-storage/ |
| WILD | B2 | U | 2026 | url | fab | — | https://cryptoadventure.com/web3-storage-review-2026-storacha-ucan-spaces-and-ipfs-plus-filecoin-storage/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://noopsschool.com/blog/artifact-repository/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://noopsschool.com/blog/immutable-artifacts/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9665304 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7640406 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/7599971 |
| WILD | B3 | U | — † | — | fab | — | https://lesitedefrancois.be/en/security/oras/ |

### 8.2.3

**Q:** Stores: admitted outputs (5.2), delivered artifacts (5.3), eval datasets (6.2), promotion bundles (7.4)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://deepwiki.com/pikachu444/cae-material-platform/7.3-artifact-storage-and-s3-integration |
| primary | B3 | T2 | — † | — | fab | — | https://docs.zenml.io/stacks/stack-components/artifact-stores |
| primary | B3 | T2 | — † | — | fab | — | https://docs.zenml.io/stack-components/artifact-stores |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/SocioProphet/model-governance-ledger |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/zavora-ai/mcp-artifact-store |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/elevata-labs/elevata/blob/main/docs/environment_promotion.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Keith-CY/dataset-warehouse |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/docs/latest/tracking/artifacts-stores |
| primary | B3 | T2 | — † | — | fab | 8.4.1 | https://mlflow.org/docs/latest/self-hosting/architecture/artifact-store/ |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/docs/2.11.2/tracking/artifacts-stores.html |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/docs/3.6.0/self-hosting/architecture/artifact-store/ |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.00041 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.11030 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://www.infoq.com/news/2026/05/cloudflare-artifacts-ai-agents/ |
| research | B3 | T3 | — † | — | fab | — | https://blog.cloudflare.com/artifacts-git-for-agents-beta/ |
| WILD | B2 | U | 2026 | url | fab | — | https://2026.cgo.org/track/cgo-2026-artifact-evaluation |
| WILD | B2 | U | 2026 | url | fab | — | https://ches.iacr.org/2026/artifacts.php |
| WILD | B2 | U | 2026 | url | fab | — | https://conf.researchr.org/track/icsa-2026/icsaartifacts+evaluation+track2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://conf.researchr.org/track/ase-2026/ase-2026-artifact-evaluation |
| WILD | B2 | U | 2026 | url | fab | — | https://www.usenix.org/conference/osdi26/call-for-artifacts |
| WILD | B3 | U | — † | — | fab | — | https://www.aiuniverse.xyz/top-10-model-registry-artifact-stores-features-pros-cons-comparison/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9880837 |
| WILD | B3 | U | — † | — | fab | — | https://kiroframe.com/mlops-artifacts-data-model-code/ |

### 8.2.4

**Q:** Retention and legal hold per data class.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-09-08 | exc | kim | — | https://aws.amazon.com/about-aws/whats-new/2026/09/amazon-s3-object-lock-variable-retention/ |
| primary | B3 | T2 | — † | — | fab | — | https://aws.amazon.com/s3/features/object-lock/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.amazonaws.cn/en_us/AmazonS3/latest/userguide/object-lock.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops-retention-date.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentsec05-bp01.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentops05-bp03.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.netapp.com/us-en/storagegrid/ilm/how-object-retention-is-determined.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingretentionrules.htm |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/azure/storage/blobs/immutable-storage-overview |
| research | B2 | T3 | 2026-02-17 | url | fab | — | https://oneuptime.com/blog/post/2026-02-17-how-to-configure-object-hold-policies-in-google-cloud-storage-for-compliance/view |
| research | B3 | T3 | — † | — | fab | — | https://aws.amazon.com/blogs/storage/applying-amazon-s3-object-lock-at-scale-for-petabytes-of-existing-data/ |
| research | B3 | T3 | — † | — | kim | — | https://www.kriv.ai/articles/delta-lake-legal-hold-and-retention-for-audits |
| research | B3 | T3 | — † | — | kim | — | https://www.solix.com/products/answers/data-lake-legal-hold-and-retention-architecture/ |
| research | B3 | T3 | — † | — | kim | — | https://specswriter.com/knowledge/what_is_an_enterprise_software_retention_framework_and_how_do_you_build_one_for_saas_and_ai_systems_in_2026.php |
| WILD | B2 | U | 2026 | exc | fab | — | https://infinisynapse.com/en/blog/data-retention-policy |
| WILD | B3 | U | — † | — | fab | — | https://academy.cegedim.cloud/storage/object-storage/object-storage-features/object-lock |
| WILD | B3 | U | — † | — | fab | — | https://batesonlaw.com/data-retention-policy-legal-requirements/ |
| WILD | B3 | U | — † | — | fab | — | https://www.letsupdateskills.com/tutorials/aws/object-lock |
| WILD | B3 | U | — † | — | fab | — | https://repost.aws/questions/QUSZMwke3uSu226EuuNnaVzg/s3-object-lock-legal-holds-vs-retention-period |
| WILD | B3 | U | — † | — | fab | — | https://www.trendmicro.com/trendaivisiononecloudriskmanagement/knowledge-base/aws/S3/object-lock.html |

### 8.3.1

**Q:** Vector/RAG port — no standard API: index / search / delete; hybrid search required?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://deepwiki.com/agno-agi/agno/5.2-vector-database-integrations |
| primary | B3 | T2 | — † | — | cur | — | https://docs.barrel-db.eu/vectordb/api/http/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/vector-search/about-hybrid-search |
| primary | B3 | T2 | — † | — | cur | — | https://docs.databricks.com/api/vector-search/v1/vector-index |
| primary | B3 | T2 | — † | — | kim | — | https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/ |
| primary | B3 | T2 | — † | — | fab | — | https://gepa-ai.github.io/gepa/api/adapters/RAGAdapter/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/pgvector/pgvector |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/MarcelRoozekrans/Rag.NET/blob/main/docs/guide/vector-stores.md |
| primary | B3 | T2 | — † | — | fab | — | https://www.meilisearch.com/products/rag |
| primary | B3 | T2 | — † | — | kim | — | https://portico.build/ports/vector_store/ |
| primary | B3 | T2 | — † | — | kim | — | https://pypi.org/project/vecport/ |
| research | B2 | T3 | 2026 | url | fab | — | https://redis.io/blog/vector-search-database-news-2026-guide/ |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.16402 |
| research | B2 | T3 | 2026-04 | exc | fab kim | — | https://supermemory.ai/blog/hybrid-search-guide/ |
| research | B2 | T3 | 2026-03 | url | fab | 10.6.3 | https://arxiv.org/pdf/2603.04444 |
| research | B2 | T3 | 2026-01 | url | fab | — | https://arxiv.org/pdf/2601.01937 |
| research | B3 | T3 | 2025-10 | url | fab | — | https://arxiv.org/pdf/2510.10123 |
| research | B3 | T3 | 2025-05 | url | fab | — | https://arxiv.org/pdf/2505.18458 |
| research | B3 | T3 | 2024-11 | url | fab | — | https://arxiv.org/pdf/2411.11895 |
| research | B3 | T3 | 2024-10 | url | fab | — | https://arxiv.org/pdf/2410.15944 |
| research | B3 | T3 | — † | — | kim | — | https://www.arxiv.org/pdf/2601.06727 |
| WILD | B1 | U | 2026-08 | exc | fab | — | https://mastra.ai/articles/best-vector-database-providers |
| WILD | B3 | U | — † | — | fab | — | https://learnopencv.com/vector-db-and-rag-pipeline-for-document-rag/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@kacperwlodarczyk/we-added-full-rag-to-our-open-source-ai-template-4-vector-stores-hybrid-search-and-reranking-696c630adbe1 |
| WILD | B3 | U | — † | — | cur | — | https://stackoverflow.com/questions/79795559/hybrid-search-on-postgres-with-pgvector-using-vecs |

### 8.3.2

**Q:** Embedding model coupling: re-embed strategy when the model changes.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-in/answers/questions/5912134/how-to-migrate-the-azure-search-index-with-latest |
| research | B1 | T3 | 2026-07-05 | url | fab | — | https://tianpan.co/blog/2026/07/05/retiring-an-embedding-model-reindex-without-downtime |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.02800 |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.05480 |
| research | B2 | T3 | 2026-04 | exc | fab | — | https://medium.com/google-cloud/migrating-vector-embeddings-in-production-without-downtime-8a0464af6f55 |
| research | B2 | T3 | 2026-04-23 | url | kim | — | https://tianpan.co/blog/2026/04/23/embedding-rotation-database-migration-not-deploy |
| research | B2 | T3 | 2026-04-09 | url | fab | — | https://tianpan.co/blog/2026-04-09-embedding-models-production-versioning-index-drift |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.24556 |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/pdf/2602.15850 |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.23471 |
| research | B3 | T3 | — † | — | cur kim | — | https://chiraghasija.cc/posts/embedding-model-versioning-rag-production-2026/ |
| research | B3 | T3 | — † | — | cur kim | — | https://dreaming.press/posts/how-to-migrate-embedding-models-in-production.html |
| research | B3 | T3 | — † | — | cur fab | — | https://medium.com/data-science-collective/different-embedding-models-different-spaces-the-hidden-cost-of-model-upgrades-899db24ad233 |
| research | B3 | T3 | — † | — | cur kim | — | https://multigrid.ai/learn/re-embedding-migration |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/vector-table-migrations |
| research | B3 | T3 | — † | — | kim | — | https://mydba.dev/blog/pgvector-production-guide |
| research | B3 | T3 | — † | — | cur | — | https://theneuralbase.com/embeddings/learn/advanced/re-embedding-on-model-upgrade/ |
| WILD | B2 | U | 2026 | url | fab | — | https://tensoria.fr/en/blog/embedding-models-2026-guide |
| WILD | B2 | U | 2026-03 | exc | fab | — | https://medium.com/@kandaanusha/vector-database-reindexing-pipeline-87efa1d1cd19 |
| WILD | B3 | U | — † | — | fab | — | https://hackernoon.com/your-embedding-model-will-deprecate-heres-what-to-do |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12541493 |

### 8.3.3

**Q:** Chunking and ingestion ownership; freshness / invalidation.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://unstructured.io/insights/rag-pipeline-best-practices-enterprise |
| research | B2 | T3 | 2026 | url | fab | — | https://www.kapa.ai/blog/how-to-build-a-rag-pipeline-from-scratch-in-2026 |
| research | B2 | T3 | 2026-05-06 | url | kim | — | https://tianpan.co/blog/2026/05/06/rag-knowledge-freshness-tiered-reindex-staleness |
| research | B2 | T3 | 2026-04-15 | url | kim | — | https://tianpan.co/blog/2026/04/15/stale-retrieval-rag-data-quality |
| research | B2 | T3 | 2026-04-10 | url | fab | — | https://tianpan.co/blog/2026/04/10/rag-freshness-problem-stale-embeddings-silent-failure |
| research | B3 | T3 | — † | — | cur | — | https://activewizards.com/blog/when-enterprise-rag-needs-a-data-owner-not-another-vector-database/ |
| research | B3 | T3 | — † | — | fab | — | https://www.automq.com/blog/rag-ingestion-freshness-without-stale-batch-context-a-real-time-architecture-playbook |
| research | B3 | T3 | — † | — | cur fab kim | — | https://blogs.oracle.com/developers/how-to-detect-rag-index-drift-deleted-docs-stale-chunks-and-duplicate-embeddings |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/alaikrm/the-data-ingestion-pipeline-nobody-designs-well-until-production-breaks-it-4l0f |
| research | B3 | T3 | — † | — | fab kim | — | https://hackernoon.com/why-better-rag-starts-with-better-ingestion |
| research | B3 | T3 | — † | — | cur kim | — | https://thomasthelliez.com/blog/rag-governance-source-authority-access-control-auditability/ |
| research | B3 | T3 | — † | — | fab | — | https://unstructured.io/insights/rag-pipeline-challenges-from-data-ingestion-to-retrieval |
| research | B3 | T3 | — † | — | kim | — | https://www.wickedsmartdata.com/articles/temporal-reasoning-in-rag-handling-document-freshness-version-conflicts-and-time-sensitive-retrieval-in-production |
| WILD | B2 | U | 2026 | url | fab | — | https://ai-business-solutions.contentwave.net/article/build-a-compliant-auditable-rag-pipeline-2026-update |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/rag-architecture/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/chunking-strategies-rag/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/rag-system-production-30-60-90-day-plan-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://medium.com/data-science-collective/modern-rag-in-2026-the-components-that-actually-matter-3f6a138ef117 |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/derrickryangiggs/rag-pipeline-deep-dive-ingestion-chunking-embedding-and-vector-search-2877 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@kakadechaitanya77/the-rag-pipeline-a-guide-to-prompts-ingestion-and-chunking-e2da562daefe |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@derrickryangiggs/rag-pipeline-deep-dive-ingestion-chunking-embedding-and-vector-search-abd3c8bfc177 |
| WILD | B3 | U | — † | — | fab | — | https://qaskills.sh/blog/rag-testing-index-freshness-staleness |

### 8.3.4

**Q:** Holdout sets (7.3) excluded from indexing — how enforced?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/AgentPostmortem/VaultRAG |
| research | B1 | T3 | 2026-07 | exc | fab | — | https://www.openlayer.com/blog/rag-pipeline-evaluation-groundedness-faithfulness |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.29797 |
| research | B2 | T3 | 2026-04-17 | url | cur kim | 10.1.6 cursor:8.3.4 | https://tianpan.co/blog/2026/04/17/vector-store-access-control-rag-rls |
| research | B2 | T3 | 2026-02 | url | fab | — | https://arxiv.org/html/2602.17234 |
| research | B2 | T3 | 2026-01 | url | fab | — | https://arxiv.org/pdf/2601.06103 |
| research | B3 | T3 | 2025-08 | url | fab | — | https://arxiv.org/html/2508.13180 |
| research | B3 | T3 | 2025-08 | url | fab | — | https://arxiv.org/pdf/2508.01059 |
| research | B3 | T3 | 2024-10 | url | fab | — | https://arxiv.org/pdf/2410.08801 |
| research | B3 | T3 | — † | — | kim | — | https://qajobfit.com/resources/build-adversarial-rag-evaluation-dataset |
| research | B3 | T3 | — † | — | kim | — | https://vorplabs.com/workflows/knowledge/rag-evaluation-dataset-design |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/how-to-evaluate-rag-systems-explained/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/glossary/holdout-data/ |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/what-is-retrieval-augmented-generation-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://nandigamharikrishna.substack.com/p/how-to-evaluate-rag-systems-accurately |
| WILD | B3 | U | 2025 | url | fab | — | https://futureagi.com/blog/rag-evaluation-metrics-2025/ |
| WILD | B3 | U | — † | — | fab | — | https://valnox.ai/en/blog/evaluating-rag |

### 8.3.5

**Q:** Store selection (pgvector, Qdrant, Weaviate, Milvus).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://assets.publishing.service.gov.uk/media/5a789c3ae5274a277e68e108/Assessment_of_Software_for_Government_v1_0.pdf |
| primary | B3 | T2 | — † | — | cur | — | https://www.cms.gov/tra/Application_Development/AD_0230_Open_Source_Business_Rules.htm |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/topk-io/bench |
| primary | B3 | T2 | — † | — | cur | — | https://kenimoto.dev/products/rag-retriever-bench/ |
| research | B1 | T3 | 2026-09-07 | exc | gpt | — | https://sukruyusufkaya.com/en/blog/vektor-veritabani-karsilastirma-pgvector-qdrant-milvus-2026 |
| research | B1 | T3 | 2026-09-07 | exc | gpt | — | https://sukruyusufkaya.com/en/blog/vektor-veritabani-karsilastirmasi-2026 |
| research | B1 | T3 | 2026-09-06 | exc | gpt | — | https://aiworkflowlab.dev/article/pinecone-vs-weaviate-vs-qdrant-vs-milvus-2026 |
| research | B1 | T3 | 2026-09-06 | exc | gpt | — | https://www.onesourcecloud.net/cms/milvus-vs-qdrant-weaviate-enterprise-rag.html |
| research | B1 | T3 | 2026-08-20 | exc | gpt | — | https://sukruyusufkaya.com/en/blog/vektor-veritabani-karsilastirma |
| research | B1 | T3 | 2026-08-13 | url | gpt | — | https://arxiv.org/abs/2608.12812 |
| research | B1 | T3 | 2026-07-01 | exc | gpt | — | https://fp8.co/articles/Vector-Database-Comparison-pgvector-Pinecone-Qdrant-Weaviate-Milvus |
| research | B1 | T3 | 2026-06-24 | exc | gpt | — | https://www.misar.blog/%40synor/articles/best-open-source-vector-database |
| research | B1 | T3 | 2026-06-22 | exc | fab gpt | — | https://www.learnersink.com/blog/vector-databases-comparison-2026 |
| research | B2 | T3 | 2026 | exc | fab kim | — | https://www.kalviumlabs.ai/blog/vector-databases-compared-pgvector-pinecone-qdrant-weaviate/ |
| research | B2 | T3 | 2026-05-19 | exc | gpt | — | https://cloud.layerbase.com/blog/vector-databases-compared-2026 |
| research | B2 | T3 | 2026-04-28 | exc | gpt | — | https://www.pccvdi.com/insights/vector-databases-compared-2026 |
| research | B2 | T3 | 2026-04-22 | exc | fab kim gpt | — | https://aiml.qa/vector-database-comparison-2026/ |
| research | B2 | T3 | 2026-03-23 | exc | gpt | — | https://www.nofluff.pro/blog/vector-database-comparison-2026 |
| research | B2 | T3 | 2026-03-11 | exc | gpt | — | https://blog.elest.io/qdrant-vs-weaviate-vs-milvus-which-vector-database-for-your-rag-pipeline/ |
| research | B2 | T3 | 2026-03-09 | exc | fab gpt | — | https://encore.dev/articles/best-vector-databases |
| research | B2 | T3 | 2026-03-07 | exc | gpt | — | https://letsbuildsolutions.com/blog/ai-ml/vector-databases-compared-what-to-use-and-when/ |
| research | B2 | T3 | 2026-03-05 | exc | kim gpt | — | https://semantic.io/insights/vector-database-comparison-2026 |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/rahul_shrivastava_1d3d4ac/the-vector-store-question-that-changes-your-entire-rag-architecture-15la |
| research | B3 | T3 | — † | — | cur | — | https://doi.org/10.4018/jsita.2011010104 |
| research | B3 | T3 | — † | — | cur | — | https://entexis.in/how-to-pick-a-vector-database-and-when-you-do-not-need-one |
| research | B3 | T3 | — † | — | gpt | — | https://islamgamal.com/blog/vector-databases-compared-2026 |
| research | B3 | T3 | — † | — | cur | — | https://www.kitware.com/how-to-evaluate-open-source-tools-for-your-team/ |
| research | B3 | T3 | — † | — | fab kim | — | https://lushbinary.com/blog/vector-database-comparison-rag-qdrant-weaviate-milvus/ |
| research | B3 | T3 | — † | — | cur | — | https://pulserevops.com/ai-infrastructure/ai339 |
| research | B3 | T3 | — † | — | kim | — | https://tomodahinata.com/en/blog/pgvector-vs-pinecone-qdrant-weaviate-milvus-vector-database-comparison-guide |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.datacamp.com/blog/the-top-5-vector-databases |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/vector-databases-for-ai-agents-pinecone-qdrant-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.firecrawl.dev/blog/best-vector-databases |
| WILD | B2 | U | 2026 | exc | fab | — | https://medium.com/@pratik-rupareliya/top-15-vector-databases-in-2026-a-production-decision-guide-from-100-enterprise-deployments-dd58a04f51a5 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.salttechno.ai/datasets/vector-database-performance-benchmark-2026/ |
| WILD | B3 | U | 2025 | url | fab | — | https://tensorblue.com/blog/vector-database-comparison-pinecone-weaviate-qdrant-milvus-2025 |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/kencho/vector-database-performance-compared-pgvector-vs-pinecone-vs-qdrant-vs-weaviate-2ne6 |
| WILD | B3 | U | — † | — | fab | — | https://tensoria.fr/en/blog/vector-database-comparison |

### 8.4.1

**Q:** Boundary: what lives here vs execution state (4.3) vs artifacts (8.2)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab kim | 8.4.2 | https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/ml-metadata/introduction |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/tensorflow/tfx/issues/4149 |
| primary | B3 | T2 | — † | — | fab | 8.4.2 | https://github.com/google/ml-metadata/blob/master/ml_metadata/proto/metadata_store_service.proto |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/bijux/bijux-canon/blob/main/docs/06-bijux-canon-runtime/interfaces/artifact-contracts.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/zavora-ai/mcp-artifact-store/blob/main/SPEC.md |
| primary | B3 | T2 | — † | — | cur | — | https://mcpboundary.com/docs/core/terminology |
| primary | B3 | T2 | — † | — | cur | — | https://mcpboundary.com/docs/core/how-it-works |
| primary | B3 | T2 | — † | — | cur | — | https://mcpboundary.com/docs/core/why-boundaries |
| primary | B3 | T2 | — † | — | fab | 8.4.2 | https://www.tensorflow.org/tfx/guide/mlmd |
| research | B2 | T3 | 2026 | exc | fab | — | https://northflank.com/blog/code-execution-environment-for-autonomous-agents |
| research | B2 | T3 | 2026 | exc | fab | — | https://northflank.com/blog/ephemeral-execution-environments-ai-agents |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.20683 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.15215 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.06365 |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/@shriomtripathi33/artifact-storage-at-scale-the-object-store-behind-build-and-deploy-6cfb12314c21 |
| research | B3 | T3 | — † | — | kim | — | https://medium.com/google-cloud/architectural-blueprint-data-decoupling-principles-and-patterns-263316175c50 |
| research | B3 | T3 | — † | — | cur | — | https://tyk.io/learning-center/what-is-mcp-registry/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.beam.cloud/blog/best-stateful-sandbox-code-execution-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.puppyone.ai/en/blog/best-ai-agent-memory-platforms |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10296296 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10127027 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10628145 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10459774 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10481874 |
| WILD | B3 | U | — † | — | cur | — | https://nhimg.org/faq/what-is-the-difference-between-an-mcp-registry-and-an-mcp-gateway/ |

### 8.4.2

**Q:** Holds: terminal job state (5.3), eval results (6.2), lineage index (6.3), artifact metadata (8.2)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://codelabs.developers.google.com/vertex-mlmd-pipelines |
| primary | B3 | T2 | — † | — | fab | — | https://docs.datahub.com/docs/generated/ingestion/sources/vertexai |
| primary | B3 | T2 | — † | — | fab | — | https://docs.mlrun.org/en/v1.0.0/store/artifacts.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.mlrun.org/en/stable/store/artifacts.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/google/ml-metadata/blob/b4891cf4f00a6d6d4b6a28a69c5601f1a48cd9f1/ml_metadata/proto/metadata_store.proto |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/hewlettpackard/cmf |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/noetl/ai-meta/issues/146 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/yarikoptic/metaxy |
| primary | B3 | T2 | — † | — | kim | — | https://nokv.io/ |
| primary | B3 | T2 | — † | — | cur kim | cursor:6.2.2 | https://tensorflow.github.io/tfx/guide/mlmd/ |
| research | B1 | T3 | 2026-09-08 | url | fab | — | https://oneuptime.com/blog/post/2026-09-08-batch-streaming-lineage-one-metadata-graph/view |
| research | B1 | T3 | 2026-09-08 | url | fab | — | https://oneuptime.com/blog/post/2026-09-08-keep-data-lineage-catalog-fresh/view |
| research | B1 | T3 | 2026-09-07 | url | fab | — | https://oneuptime.com/blog/post/2026-09-07-lineage-impact-analysis-ci/view |
| research | B2 | T3 | 2026-02-17 | url | fab | — | https://oneuptime.com/blog/post/2026-02-17-how-to-track-ml-metadata-and-lineage-with-vertex-ai-ml-metadata/view |
| WILD | B3 | U | — † | — | fab | — | https://agility-at-scale.com/ai/data/data-lineage-and-metadata-management/ |
| WILD | B3 | U | — † | — | fab | — | https://akshaykapoor020.medium.com/artifacts-metadata-and-data-lineage-in-mlops-58e8aa0a3b40 |
| WILD | B3 | U | — † | — | fab | — | https://datawarehouseinfo.com/practice/data-warehouse-metadata/ |
| WILD | B3 | U | — † | — | fab | — | https://wiki.adhadse.com/ml/mle-for-production/ml-data-lifecycle/week3/ |

### 8.4.3

**Q:** Database behind a repository interface; schema migration policy.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/raaymax/quack/blob/dev/docs/adr/014-repository-pattern-over-orm.md |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/bytepark/lib-migration |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/zitadel/nextgen/blob/main/docs/adrs/028-storage-v2-statements-and-dialects.md |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design |
| primary | B3 | T2 | — † | — | cur | — | https://typeorm.io/docs/migrations/why |
| research | B2 | T3 | 2026 | exc | fab | — | https://www.bytebase.com/blog/top-database-schema-change-tool-evolution/ |
| research | B2 | T3 | 2026-03-25 | url | fab kim | — | https://ardentperf.com/2026/03/25/database-schema-migrations-in-2026-survey/ |
| research | B3 | T3 | — † | — | fab | — | https://amasucci.com/posts/database-migrations-best-practices/ |
| research | B3 | T3 | — † | — | cur | — | https://binarylog.dev/post/designing-a-clean-persistence-layer-in-go-with-ports-pools-and-migrations |
| research | B3 | T3 | — † | — | fab | — | https://dbschema.com/blog/migrations/open-source-schema-migration-tools/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/cristiansifuentes/repository-pattern-vs-direct-dbcontext-usage-in-net-2026-edition-31pd |
| research | B3 | T3 | — † | — | cur | — | https://dulanwirajith.medium.com/when-good-decisions-outlive-their-context-a-typeorm-migration-story-d105fe358680 |
| research | B3 | T3 | — † | — | fab | — | https://enterprisecraftsmanship.com/posts/should-you-abstract-database/ |
| research | B3 | T3 | — † | — | fab | — | https://www.qovery.com/blog/database-schema-migrations-in-ephemeral-environments-best-practices |
| research | B3 | T3 | — † | — | kim | — | https://the-runtime.dev/articles/repository-pattern-when-and-when-not/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://khimananda.com/blog/database-migrations-in-ci-cd-pipelines |
| WILD | B3 | U | 2025 | url | fab | — | https://www.dbvis.com/thetable/top-database-cicd-and-schema-change-tools-in-2025/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/jefersoneiji/best-practices-for-database-schema-migrations-in-large-systems-4nl9 |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/schema-migration?o=desc&s=updated |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/database-schema-migration |
| WILD | B3 | U | — † | — | fab | — | https://www.postgresql.org/message-id/58EA6FBC-03C4-11D9-8609-000D93AE0944%40sitening.com |
| WILD | B3 | U | — † | — | cur | — | https://softwareengineering.stackexchange.com/questions/271610/how-to-implement-the-repository-pattern-for-an-app-that-will-change-its-database |

### 8.4.4

**Q:** Catalog model — reuse OpenLineage / OpenMetadata entities?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/OpenLineage/openlineage-site/blob/main/versioned_docs/version-1.48.0/spec/object-model.md |
| core | B3 | T1 | — † | — | cur | — | https://openlineage.io/docs/spec/facets/custom-facets/ |
| primary | B3 | T2 | — † | — | cur | — | https://cdn.jsdelivr.net/npm/pi-multica-spine@0.12.8/lib/workflow-catalog.ts |
| primary | B3 | T2 | — † | — | fab kim | — | https://docs.open-metadata.org/v1.13.x/connectors/pipeline/openlineage |
| primary | B3 | T2 | — † | — | fab | — | https://docs.open-metadata.org/v1.12.x/connectors/pipeline/openlineage |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/stencila/stencila/blob/main/schema/Workflow.yaml |
| primary | B3 | T2 | — † | — | fab | 8.4.5 | https://github.com/open-metadata/openmetadata |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/open-metadata/OpenMetadata/releases |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/open-metadata/OpenMetadata/releases/tag/1.12.9-release |
| primary | B3 | T2 | — † | — | fab | — | https://open-metadata.org/ |
| primary | B3 | T2 | — † | — | fab | — | https://open-metadata.org/product-updates |
| primary | B3 | T2 | — † | — | cur | — | https://snakemake.github.io/snakemake-workflow-catalog/docs/catalog.html |
| research | B1 | T3 | 2026-09-08 | url | fab | — | https://oneuptime.com/blog/post/2026-09-08-choose-openlineage-datahub-openmetadata-column-lineage/view |
| research | B3 | T3 | — † | — | fab kim | — | https://atlan.com/openmetadata-vs-openlineage/ |
| WILD | B3 | U | — † | — | fab | — | https://en.wikipedia.org/wiki/Entity_Framework |
| WILD | B3 | U | — † | — | fab | — | https://pipecode.ai/blogs/openlineage-openmetadata-open-standards-lineage-catalog |

### 8.4.5

**Q:** Export path for the whole catalog.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://community.denodo.com/docs/html/browse/9.2/en/vdp/data_catalog/administration/import_export/import_export |
| primary | B3 | T2 | — † | — | fab | — | https://developer.bigid.com/wiki/BigID_API/Metadata_Export_Tutorial |
| primary | B3 | T2 | — † | — | kim | — | https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/export-asset-metadata.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.bentley.com/LiveContent/web/Promis.e-v2026/Help/en/topics/1436924/GUID-9C88B23C-D411-4C7F-833D-AD8E9925584B.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.cloud.google.com/dataplex/docs/export-metadata?authuser=0 |
| primary | B3 | T2 | — † | — | kim | — | https://docs.databricks.com/aws/en/security/privacy/export-workspace-data |
| primary | B3 | T2 | — † | — | fab | — | https://docs.open-metadata.org/v1.7.x/how-to-guides/data-discovery/export |
| primary | B3 | T2 | — † | — | fab | — | https://docs.open-metadata.org/v1.12.x/how-to-guides/data-discovery/export |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/Azure-Samples/data-catalog-dotnet-import-export |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/bdgscotland/omd_migrate |
| primary | B3 | T2 | — † | — | fab | — | https://guides.dataverse.org/en/latest/admin/metadataexport.html |
| primary | B3 | T2 | — † | — | cur | — | https://help.hcl-software.com/commerce/9.1.0/admin/tasks/tpncatalogexport.html |
| primary | B3 | T2 | — † | — | kim | — | https://projectnessie.org/guides/migration/ |
| primary | B3 | T2 | — † | — | kim | — | https://support.datahub.com/hc/en-us/articles/41912143140379-Metadata-Import-Export-and-Backup |
| research | B3 | T3 | — † | — | fab | — | https://www.decube.io/post/bulk-metadata-made-simple-with-export-import |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.modern-datatools.com/tools/openmetadata |
| WILD | B2 | U | 2026-05 | url | fab | — | https://sfdcfileexporter.com/blog/2026/05/salesforce-bulk-data-export-documentation.html |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/openmetadata-explained/ |
| WILD | B3 | U | — † | — | fab | — | https://dataworkers.io/resources/openmetadata/ |
| WILD | B3 | U | — † | — | cur | — | https://diskcatalogmaker.com/es/faq/exporttext.html |
| WILD | B3 | U | — † | — | cur | — | https://www.extrabit.com/guides/generate-file-inventory |
| WILD | B3 | U | — † | — | cur | — | https://github.laiyagushi.com/Shintaro-Sugawara/PathList |
| WILD | B3 | U | — † | — | fab | — | https://openmetadatastandards.org/ |
| WILD | B3 | U | — † | — | fab | — | https://pipeline2insights.substack.com/p/introduction-to-openmetadata-an-open-source-data-catalog-solution |

### 8.5.1

**Q:** Registered entities: models, prompts, tools (MCP servers), datasets, agents, bundles — one registry or per type?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-07-20 | url | cur | — | https://pkg.go.dev/github.com/tesserix/agentic-registry@v0.0.0-20260720231510-1cab4f816df0 |
| primary | B2 | T2 | 2026-02-05 | url | fab | — | https://www.apicur.io/blog/2026/02/05/apicurio-registry-ai-natural-evolution |
| primary | B3 | T2 | — † | — | cur fab kim | — | https://aws.amazon.com/blogs/machine-learning/manage-agents-tools-and-skills-at-scale-with-aws-agent-registry/ |
| primary | B3 | T2 | — † | — | cur kim | — | https://github.com/agentregistry-dev/agentregistry/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/agentic-community/mcp-gateway-registry/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Haibread/ai-registry |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/agentregistry-dev/agentregistry |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ara-registry/spec |
| primary | B3 | T2 | — † | — | fab | — | https://www.harness.io/products/artifact-registry |
| primary | B3 | T2 | — † | — | fab | — | https://jfrog.com/ai-catalog/mcp-registry/ |
| primary | B3 | T2 | — † | — | fab | — | https://konghq.com/blog/product-releases/kong-mcp-registry-tech-preview |
| primary | B3 | T2 | — † | — | gpt | 8.5.2 | https://prod.registry.modelcontextprotocol.io/ |
| primary | B3 | T2 | — † | — | fab gpt | 8.5.2 8.5.5 | https://registry.modelcontextprotocol.io/ |
| primary | B3 | T2 | — † | — | fab | — | https://wandb.ai/site/registry/ |
| research | B3 | T3 | 2025-08 | url | fab | — | https://arxiv.org/pdf/2508.18489 |
| research | B3 | T3 | 2025-05 | url | fab | — | https://arxiv.org/pdf/2505.10609 |
| research | B3 | T3 | — † | — | fab | — | https://www.alation.com/blog/ai-model-registry/ |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2510.03495v2 |
| research | B3 | T3 | — † | — | kim | — | https://atlan.com/know/ai-agent/agent-registry-vs-mcp-registry/ |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/agent-registry-vs-mcp-registry-discovery.html |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/ai-agent/agent-registry-vs-model-registry/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://atlan.com/know/ai-agent/what-is-an-ai-agent-registry/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/mcp-adoption-statistics-2026-model-context-protocol |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.exploreagentic.ai/agent-registry/ |
| WILD | B2 | U | 2026 | exc | fab | 8.5.3 | https://www.truefoundry.com/blog/best-mcp-registries |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12536406 |
| WILD | B3 | U | — † | — | fab | — | https://www.truefoundry.com/blog/ai-agent-registry |

### 8.5.2

**Q:** MCP Registry spec for tools (3.5); A2A Agent Cards (1.5) for agents; OCI for bundles? Which format governs prompt and dataset entries, where no registry spec exists?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/generic-server-json.md |
| core | B3 | T1 | — † | — | kim | — | https://modelcontextprotocol.io/registry/package-types.md |
| core | B3 | T1 | — † | — | kim | — | https://specification.website/spec/agent-readiness/a2a-agent-cards |
| primary | B3 | T2 | — † | — | cur fab kim | cursor:8.5.2 | https://docs.cloud.google.com/agent-registry/json-schemas |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2508.03095v3 |
| research | B3 | T3 | — † | — | fab | — | https://www.speakeasy.com/mcp/release-notes |
| WILD | B2 | U | 2026 | url | fab | — | https://mcpplaygroundonline.com/blog/mcp-stateless-2026-release-candidate |
| WILD | B2 | U | 2026 | exc | fab | — | https://nerdleveltech.com/agentic-resource-discovery-ard-aws-agent-registry |
| WILD | B2 | U | 2026 | exc | fab | 8.5.3 | https://roxyapi.com/blogs/mcp-registries-where-to-list-your-server |

### 8.5.3

**Q:** Is the registry the tool discovery source for 3.5, or is discovery static config?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | kim | — | https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/2413 |
| primary | B3 | T2 | 2025-09-08 | url | fab | — | https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/ |
| primary | B3 | T2 | — † | — | gpt | 8.5.4 8.5.5 10.2.5 | https://aws-samples.github.io/sample-autonomous-cloud-coding-agents/decisions/adr-022-agent-asset-registry/ |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/prescriptive-guidance/latest/mcp-strategies/mcp-tool-strategy-discovery.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.cloud.google.com/agent-registry/manage-mcp-tools |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/agentic-community/mcp-gateway-registry/blob/main/docs/dynamic-tool-discovery.md |
| primary | B3 | T2 | — † | — | fab | — | https://konghq.com/products/mcp-registry |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/plugin-dynamic-tool-discovery |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/microsoftteams/platform/m365-apps/agent-connectors |
| primary | B3 | T2 | — † | — | fab | 8.5.5 | https://learn.microsoft.com/en-us/azure/api-center/register-discover-mcp-server |
| primary | B3 | T2 | — † | — | fab kim | — | https://www.truefoundry.com/blog/mcp-tool-discovery-for-enterprise-ai-agents |
| research | B3 | T3 | — † | — | kim | — | https://gingerlabs.ai/blog/mcp-server-discovery-registry-server-cards |
| research | B3 | T3 | — † | — | kim | — | https://groundy.com/articles/mcp-tool-discovery-moves-from-hardcoded-config-to-runtime-agent-search/ |
| research | B3 | T3 | — † | — | fab | — | https://konghq.com/blog/engineering/mcp-registry-dynamic-tool-discovery |
| research | B3 | T3 | — † | — | kim | — | https://nhimg.org/articles/mcp-registry-driven-tool-discovery-changes-agent-governance/ |
| research | B3 | T3 | — † | — | kim | — | https://zylos.ai/research/2026-03-21-dynamic-tool-discovery-capability-negotiation/ |
| WILD | B1 | U | 2026-07-20 | url | fab | 8.5.6 | https://digitalthoughtdisruption.com/2026/07/20/mcp-registry-discover-verify-safely-connect-servers/ |
| WILD | B1 | U | 2026-06-26 | exc | gpt | 8.5.5 | https://www.freshcrate.ai/projects/mcp-gateway-registry |
| WILD | B2 | U | 2026 | exc | fab | — | https://obot.ai/resources/learning-center/mcp-tool-discovery/ |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/@rekog-labs/MCP-Nest/blob/149a3402b36f7318d2c1704b45c1ec3bddad6c44/docs/tool-discovery-and-registration.md |
| WILD | B3 | U | — † | — | fab | — | https://konghq.com/blog/learning-center/what-is-an-mcp-registry |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@amiarora/solving-the-mcp-tool-discovery-problem-how-ai-agents-find-what-they-need-b828dbce2c30 |
| WILD | B3 | U | — † | — | fab | — | https://www.truefoundry.com/blog/centralized-mcp-registry-architecture |

### 8.5.4

**Q:** Promotion (7.4) writes here — confirmed as single source of truth?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/articles/tags/how-to-use-model-registry/ |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/articles/tags/shared-model-registry-benefits/ |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/docs/latest/ml/model-registry/ |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/articles/role-of-model-deployment-pipelines/ |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/docs/latest/ml/model-registry/workflow/ |
| primary | B3 | T2 | — † | — | kim | — | https://mlflow.org/articles/ai-model-registry-management-checklist/ |
| primary | B3 | T2 | — † | — | cur | — | https://p.rst.im/q/github.com/mizcausevic-dev/model-registry-pro |
| research | B2 | T3 | 2026-01-25 | url | fab | — | https://oneuptime.com/blog/post/2026-01-25-model-registry/view |
| research | B3 | T3 | — † | — | cur kim | — | https://dezynum.com/insights/registry-metadata-is-not-promotion-evidence |
| research | B3 | T3 | — † | — | cur kim | — | https://dezynum.com/insights/lineage-without-decision-state-fails-audits |
| research | B3 | T3 | — † | — | cur | — | https://dezynum.com/insights/model-registry-is-a-catalog-not-a-court-record |
| research | B3 | T3 | — † | — | cur | — | https://dezynum.com/insights/promotion-event-is-the-evidence |
| research | B3 | T3 | — † | — | kim | — | https://dezynum.com/insights/promotion-is-a-transaction-treat-it-like-one |
| WILD | B2 | U | 2026 | exc | fab | — | https://123ofai.com/articles/blocks/model-registry |
| WILD | B3 | U | — † | — | fab | — | https://apxml.com/courses/introduction-to-mlops/chapter-5-model-deployment-and-serving/introduction-to-model-registries |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/model-registry-implementation-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://datarekha.com/mlops/model-registry/ |
| WILD | B3 | U | — † | — | fab | 10.6.4 | https://en.wikipedia.org/wiki/Single_source_of_truth |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@faizulkhan56/mastering-mlflow-model-registry-a-complete-hands-on-guide-1309beeac333 |
| WILD | B3 | U | — † | — | fab | — | https://mlops-coding-course.fmind.dev/5.%20Refining/5.6.%20Model%20Registries.html |
| WILD | B3 | U | — † | — | fab | — | https://sysart.consulting/insights/on-premises-ai-model-registry-version-control/ |
| WILD | B3 | U | — † | — | fab | 10.6.2 | https://tutorialsdojo.com/amazon-sagemaker-model-registry-cheat-sheet/ |

### 8.5.5

**Q:** Versioning scheme and immutability; discovery API.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/openstack/api-wg/blob/master/guidelines/discoverability.rst |
| core | B3 | T1 | — † | — | cur | — | https://kubernetes.io/docs/concepts/overview/kubernetes-api/ |
| core | B3 | T1 | — † | — | fab | — | https://modelcontextprotocol.io/registry/versioning |
| primary | B3 | T2 | 2025-03-21 | url | fab | — | https://www.apicur.io/blog/2025/03/21/semantic-versioning |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/modelcontextprotocol/registry |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/apm/reference/registry-http-api/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.npmjs.com/package/semserver |
| primary | B3 | T2 | — † | — | fab | — | https://registry.modelcontextprotocol.io/docs |
| research | B1 | T3 | 2026-08 | exc | fab | — | https://buildwithfern.com/post/automating-semantic-versioning-api-sdks-claude |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.07551 |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.18536 |
| research | B3 | T3 | 2025-10 | url | fab | — | https://arxiv.org/pdf/2510.03495 |
| research | B3 | T3 | — † | — | cur | — | https://www.akamai.com/glossary/what-is-api-versioning |
| research | B3 | T3 | — † | — | fab kim | 10.7.3 | https://www.digitalapplied.com/blog/api-versioning-strategies-2026-engineering-decision-matrix |
| research | B3 | T3 | — † | — | kim | — | https://endpointsregistry.com/selecting-the-best-versioning-model-for-your-registry/ |
| research | B3 | T3 | — † | — | cur | — | https://irina.codes/api-versioning-a-deep-dive/ |
| research | B3 | T3 | — † | — | cur | — | https://pratikdhanave.com/blog/posts/api-design-05-versioning-and-evolution.html |
| research | B3 | T3 | — † | — | kim | — | https://www.techinterview.org/post/3233469426/lld-package-registry/ |
| research | B3 | T3 | — † | — | fab | — | https://workos.com/blog/mcp-registry-architecture-technical-overview |
| WILD | B2 | U | 2026 | exc | fab | — | https://devsecopsschool.com/blog/api-versioning/ |
| WILD | B3 | U | — † | — | fab | — | https://www.ai-visibility.org.uk/specifications/versioning/ |
| WILD | B3 | U | — † | — | fab | — | https://modelcontextprotocol.info/tools/registry/faq/ |
| WILD | B3 | U | — † | — | fab | — | https://talent500.com/blog/semantic-versioning-explained-guide/ |

### 8.5.6

**Q:** MCP server admission: before a server is registered (8.5) and exposed via the tool interface (3.5), is there a publisher / signature check (per the MCP Registry spec) and a sandboxed trial run, or is addition manual and unaudited?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07 | url | cur fab | cursor:3.5.3 | https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md |
| core | B3 | T1 | — † | — | kim | — | https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/server-json/official-registry-requirements.md |
| core | B3 | T1 | — † | — | fab kim | — | https://modelcontextprotocol.io/registry/authentication |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/sns45/smithmark/blob/v0.2.0/proposals/mcp-registry-provenance/RFC.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/cli/commands.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/quickstart.mdx |
| research | B2 | T3 | 2026 | exc | fab | — | https://ghost.securitywall.co/mcp-security-testing-guide/ |
| research | B2 | T3 | 2026 | exc | fab | — | https://www.networkintelligence.ai/blogs/model-context-protocol-mcp-security-checklist/ |
| research | B2 | T3 | 2026 | exc | fab | — | https://securitywall.co/blog/mcp-security-testing-guide |
| research | B3 | T3 | — † | — | fab | — | https://affine.pro/blog/mcp-registry-guide |
| research | B3 | T3 | — † | — | fab | — | https://github.blog/ai-and-ml/generative-ai/how-to-find-install-and-manage-mcp-servers-with-the-github-mcp-registry/ |
| research | B3 | T3 | — † | — | kim | — | https://www.mdpi.com/1999-5903/18/5/243 |
| research | B3 | T3 | — † | — | kim | — | https://safeguard.sh/resources/blog/mcp-server-registry-security-governance |
| WILD | B1 | U | 2026-07 | exc | fab | — | https://medium.com/@chenyuan19920509/the-old-way-of-publishing-mcp-servers-is-gone-heres-what-replaced-it-9b7e41160a8c |
| WILD | B2 | U | 2026 | exc | fab | — | https://medium.com/@MattLeads/6-critical-challenges-facing-the-mcp-in-2026-06258e914402 |
| WILD | B2 | U | 2026 | exc | fab | — | https://modal.com/resources/best-code-execution-sandboxes-mcp-servers |
| WILD | B3 | U | — † | — | fab | — | https://adambernard.com/kb/ai/methods/mcp/github-mcp-registry/ |
| WILD | B3 | U | — † | — | fab | — | https://mcpcn.com/en/tools/registry/cli/ |
| WILD | B3 | U | — † | — | fab | — | https://modelcontextprotocol.info/tools/registry/cli/ |
| WILD | B3 | U | — † | — | fab | — | https://modelcontextprotocol.info/tools/registry/publishing/ |
| WILD | B3 | U | — † | — | fab | — | https://www.synscribe.com/agentic-discovery/mcp-server-distribution |

### 8.5.7

**Q:** Deprecation and sunset: who marks a model, prompt, tool, or agent version deprecated in the registry; is it signaled to callers by a detectable contract (Deprecation / Sunset headers, RFC 9745 / RFC 8594) or a registry field only; what migration window before routing (10.6.3) refuses it?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | — | https://datatracker.ietf.org/doc/draft-ietf-httpapi-deprecation-header/09/ |
| core | B3 | T1 | — † | — | kim | — | https://datatracker.ietf.org/doc/html/rfc8594.html |
| core | B3 | T1 | — † | — | kim gpt | — | https://www.rfc-editor.org/rfc/rfc9745.html |
| core | B3 | T1 | — † | — | fab | — | https://www.rfc-editor.org/info/rfc8594/ |
| core | B3 | T1 | — † | — | gpt | — | https://www.rfc-editor.org/info/rfc9745/ |
| primary | B3 | T2 | — † | — | kim | — | https://yaniv-golan.github.io/openai-model-registry/api_reference/deprecation/ |
| research | B2 | T3 | 2026-01-30 | url | fab | — | https://oneuptime.com/blog/post/2026-01-30-api-deprecation-headers/view |
| research | B3 | T3 | — † | — | kim | — | https://changegamer.ai/resources/llm-model-deprecation |
| research | B3 | T3 | — † | — | kim | — | https://qaskills.sh/blog/api-testing-deprecation-sunset-headers |
| research | B3 | T3 | — † | — | kim | — | https://tianpan.co/blog/2026/04-27-model-deprecation-treadmill-pre-sunset-discipline |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.restguide.info/api-deprecation |
| WILD | B3 | U | — † | — | fab | — | https://anethoth.com/api-deprecation-sunset-headers/ |
| WILD | B3 | U | — † | — | fab | — | https://apis.io/providers/sunset-header/ |
| WILD | B3 | U | — † | — | fab | — | https://codelit.io/blog/api-deprecation-strategy |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/apikumo/sunset-your-api-endpoints-on-purpose-the-deprecation-and-sunset-headers-4bmh |
| WILD | B3 | U | — † | — | fab | — | https://github.com/ELares/IronTraffic/issues/375 |
| WILD | B3 | U | — † | — | fab | — | https://http.dev/sunset |
| WILD | B3 | U | — † | — | fab | — | https://loadfocus.com/glossary/what-is-api-deprecation |
| WILD | B3 | U | — † | — | fab | — | https://tagteam.harvard.edu/hub_feeds/3876/feed_items/13338981/about |
| WILD | B3 | U | — † | — | fab | — | https://zuplo.com/learning-center/http-deprecation-header |

## 9. Agentic Standards (governance of the standards themselves)

### 9.1

**Q:** Pinned version; conformance / test suite; who tracks spec changes.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | exc | kim | — | https://modelcontextprotocol.io/specification/2026-07-28/changelog |
| primary | B3 | T2 | — † | — | gpt | 9.2 | https://docs.ag-ui.com/agentic-protocols |
| primary | B3 | T2 | — † | — | cur kim | cursor:9.3.1 | https://github.com/a2aproject/a2a-tck |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Neeeophytee/mcp-stateless-conformance |
| primary | B3 | T2 | — † | — | kim | — | https://registry.npmjs.org/@a2a-compliance/cli |
| primary | B3 | T2 | — † | — | kim | 9.5 | https://ts.sdk.modelcontextprotocol.io/v2/protocol-versions.html |
| WILD | B2 | U | 2026 | exc | fab | 9.3 9.4 9.5 | https://dev.to/pockit_tools/mcp-vs-a2a-the-complete-guide-to-ai-agent-protocols-in-2026-30li |
| WILD | B2 | U | 2026 | exc | fab | — | https://jaxlondon.com/ai-development-agentic-systems/agent-protocols-mcp-a2a/ |
| WILD | B3 | U | — † | — | fab | 9.4 | https://ceaksan.com/en/ai-agent-protocols-mcp-a2a-ucp-ap2-a2ui-ag-ui |
| WILD | B3 | U | — † | — | fab | 9.3 9.4 | https://dzone.com/articles/mcp-vs-a2a-vs-agui |

### 9.2

**Q:** Maturity: governance body, breaking-change history, adoption.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-12-09 | exc | fab | — | https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation |
| core | B3 | T1 | — † | — | kim | — | https://modelcontextprotocol.io/community/governance |
| primary | B3 | T2 | 2025-12-09 | url | fab | — | https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/ |
| research | B1 | T3 | 2026-08-17 | exc | kim | — | https://packetnebula.com/articles/a2a-joins-aaif-v1-migration/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/html/2606.31498 |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.21090 |
| research | B3 | T3 | — † | — | kim | — | https://deepwiki.com/modelcontextprotocol/modelcontextprotocol/8.1-governance-structure |
| WILD | B2 | U | 2026 | url | fab | — | https://baeseokjae.github.io/posts/linux-foundation-agentic-ai-foundation-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://datalakehousehub.com/blog/state-of-agentic-ai-standards-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://dev.to/kanywst/mapping-mcp-a2a-and-acp-telling-ai-agent-protocols-apart-in-2026-1hha |
| WILD | B2 | U | 2026 | exc | fab | — | https://mcp.directory/blog/mcp-foundation-linux-foundation-aaif-2026-explained |
| WILD | B3 | U | — † | — | fab | — | https://www.adamsilvaconsulting.com/insights/agent-protocol-stack-from-data-to-ui |
| WILD | B3 | U | — † | — | fab | — | https://amdatalakehouse.substack.com/p/the-state-of-agentic-ai-standards |
| WILD | B3 | U | — † | — | fab | — | https://blckalpaca.at/en/knowledge-base/ai-agents/a2a-protocol-basics/linux-foundation-aaif-bedeutung |
| WILD | B3 | U | — † | — | fab | — | https://www.edtechinnovationhub.com/news/linux-foundation-creates-agentic-ai-foundation-to-steward-open-standards-for-autonomous-ai-systems |
| WILD | B3 | U | — † | — | fab | — | https://www.prnewswire.com/news-releases/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation-aaif-anchored-by-new-project-contributions-including-model-context-protocol-mcp-goose-and-agentsmd-302636897.html |

### 9.3

**Q:** Boundary resolution: where ACP ends and A2A begins; where AG-UI ends and ACP begins. One protocol per boundary, written down.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur kim | cursor:9.1.2 cursor:9.1.6 | https://agentcommunicationprotocol.dev/introduction/welcome |
| primary | B1 | T2 | 2026-07-20 | exc | gpt | — | https://ag-ui.ai/en/technologies/ag-ui |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/agent-protocol-stack-mcp-a2a-agui-a2ui.html |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/ag-ui-vs-mcp-vs-a2a.html |
| research | B3 | T3 | — † | — | kim | — | https://zenithlaw.com/mcp-vs-a2a-practical-protocol-boundaries-agentic-systems |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.digitalapplied.com/blog/ai-agent-protocol-ecosystem-map-2026-mcp-a2a-acp-ucp |
| WILD | B2 | U | 2026-03-20 | url | fab | — | https://www.d4b.dev/blog/2026-03-20-agentic-ui-comparing-ag-ui-mcp-ui-and-a2a-protocols |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/codetodeploy/the-agent-protocol-stack-mcp-vs-a2a-vs-ag-ui-when-to-use-what-f735a5934293 |

### 9.4

**Q:** Extension policy where the spec lacks coverage (namespaced extensions, never forks).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | exc | cur kim | 9.5 cursor:9.4.4 | https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning |
| core | B1 | T1 | 2026-07-28 | exc | kim | — | https://modelcontextprotocol.io/community/seps/2133-extensions.md |
| core | B1 | T1 | 2026-07-28 | exc | kim | — | https://modelcontextprotocol.io/extensions/overview.md |
| core | B3 | T1 | — † | — | cur gpt | cursor:9.3.4 | https://a2a-protocol.org/dev/topics/extensions/ |
| core | B3 | T1 | — † | — | cur kim | cursor:9.3.4 | https://a2a-protocol.org/v0.3.0/topics/extensions/ |
| core | B3 | T1 | — † | — | gpt | — | https://a2a-protocol.org/v0.2.6/topics/extensions/ |
| core | B3 | T1 | — † | — | cur kim | cursor:9.3.4 | https://github.com/a2aproject/A2A/blob/2183794b/docs/topics/extensions.md |
| primary | B2 | T2 | 2026-01-26 | url | fab | — | https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.16524 |
| WILD | B1 | U | 2026-07 | exc | fab | — | https://medium.com/system-design-mastery-series/ag-ui-vs-mcp-vs-a2a-vs-a2ui-a-field-guide-to-the-2026-agent-protocol-stack-07080e346fc9 |

### 9.5

**Q:** Fallback when the counterpart does not speak the protocol (adapter, or refuse).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/OrendaD/hermes-a2a-plugin |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/win4r/openclaw-a2a-gateway/tree/f2376f3b7c46a6499a0b2884cc5e89722ba6740c |
| primary | B3 | T2 | — † | — | kim | — | https://py.sdk.modelcontextprotocol.io/v2/protocol-versions/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.09751 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.03755 |
| WILD | B2 | U | 2026 | exc | fab | — | https://agentlux.ai/blog/the-agent-protocol-stack-in-2026-mcp-a2a-and-x402-explained-2 |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.buildmvpfast.com/blog/ai-engineer-stack-2026-mcp-a2a-protocol |
| WILD | B2 | U | 2026 | exc | fab | — | https://onereach.ai/blog/guide-choosing-mcp-vs-a2a-protocols/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.puppyone.ai/en/blog/agent-context-protocol |
| WILD | B3 | U | — † | — | fab | — | https://www.meta-intelligence.tech/en/insight-a2a-mcp |

### 9.6

**Q:** The model interface (3.2) rests on a de facto standard (OpenAI-compatible chat / tool-calling / structured-output conventions) with no governing body: is it version-pinned and conformance-tested like the five protocols (9.1), and who tracks breaking changes across providers?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://developers.openai.com/api/docs/guides/structured-outputs |
| primary | B3 | T2 | — † | — | kim | — | https://docs.litellm.ai/docs/completion/drop_params |
| primary | B3 | T2 | — † | — | fab | — | https://docs.vllm.ai/en/latest/features/structured_outputs/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ibidathoillah/openai-compatible-tester-cli |
| primary | B3 | T2 | — † | — | gpt | — | https://help-lb.openai.com/en/articles/8555517-function-calling-in-the-openai-api |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs |
| primary | B3 | T2 | — † | — | fab | — | https://platform.openai.com/docs/changelog |
| primary | B3 | T2 | — † | — | fab | — | https://reference.langchain.com/python/langchain-openai/chat_models/base/BaseChatOpenAI/with_structured_output |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2604.09360v1 |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/multigrid/what-openai-compatible-actually-means-for-an-endpoint-3f9f |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/seven7763/openai-compatible-is-a-spectrum-not-a-boolean-heres-an-11-check-conformance-suite-2mhj |
| research | B3 | T3 | — † | — | kim | — | https://inferbase.ai/blog/single-api-for-multiple-llm-providers |
| research | B3 | T3 | — † | — | kim | — | https://ssimplifi.com/guides/openai-compatible-api |
| WILD | B2 | U | 2026 | url | fab | — | https://apirank.vip/tutorials/gpt-5-6-api-compatibility-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/openai-compatible-api-standard-provider-agnostic-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://servicesground.com/blog/function-calling-structured-outputs/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://tokenmix.ai/blog/openai-compatible-api |
| WILD | B3 | U | — † | — | fab | — | https://ai-tldr.dev/learn/llm-apis/provider-guides/openai-compatible-apis/ |
| WILD | B3 | U | — † | — | fab | — | https://aicompetence.org/openai-compatible-api/ |
| WILD | B3 | U | — † | — | fab | — | https://blog.stackademic.com/openai-function-calling-full-guide-75d9e14db3de?gi=168679d69e26 |
| WILD | B3 | U | — † | — | fab | — | https://infron.ai/blog/openai-api-compatibility-gaps |

## 10. Cross-Cutting Concerns

### 10.1.1

**Q:** Human identity: OIDC provider. Workload/agent identity: SPIFFE/SPIRE or equivalent.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07 | exc | kim | — | https://datatracker.ietf.org/doc/draft-lundholm-kaif/ |
| core | B3 | T1 | — † | — | cur | — | https://spiffe.io/docs/latest/spiffe-specs/spiffe/ |
| core | B3 | T1 | — † | — | gpt | — | https://spiffe.io/docs/latest/spire-about/spire-concepts/ |
| core | B3 | T1 | — † | — | gpt | — | https://spiffe.io/docs/latest/deploying/spire_agent/ |
| primary | B1 | T2 | 2026-08-12 | exc | gpt | — | https://github.com/MicrosoftDocs/entra-docs/blob/main/docs/workload-id/workload-identity-federation-spiffe-spire.md |
| primary | B2 | T2 | 2026-03-03 | exc | gpt | — | https://github.com/spiffe/spire/blob/main/CHANGELOG.md |
| primary | B3 | T2 | — † | — | fab | — | https://developer.pingidentity.com/identity-for-ai/protocols/authplayground-spiffe.html |
| primary | B3 | T2 | — † | — | fab | 10.1.10 | https://github.com/inference-gateway/operator/issues/122 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Cleave360/KAIF-Public |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/spiffe/spire/blob/main/doc/scaling_spire.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/spiffe/spire/blob/main/doc/spire_agent.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/spiffe/spire/blob/main/doc/spire_agent.md?plain=1 |
| primary | B3 | T2 | — † | — | gpt | — | https://learn.microsoft.com/en-us/entra/workload-id/workload-identity-federation-spiffe-spire |
| research | B2 | T3 | 2026 | url | fab | — | https://stacklok.com/blog/agentic-identity-explained-how-to-apply-spiffe-and-relationship-based-authorization-to-ai-agents-in-2026/ |
| research | B3 | T3 | — † | — | kim | — | https://alatirok.com/spiffe-spire-ai-agents-svid-mtls/ |
| research | B3 | T3 | — † | — | fab | — | https://www.hashicorp.com/en/blog/spiffe-securing-the-identity-of-agentic-ai-and-non-human-actors |
| research | B3 | T3 | — † | — | kim | — | https://ijsrcseit.com/home/article/view/CSEIT2612335 |
| research | B3 | T3 | — † | — | cur | — | https://praesidia.ai/blog/mtls-workload-identity-spiffe-agents |
| research | B3 | T3 | — † | — | fab | 10.1.10 | https://riptides.io/blog/how-to-deliver-spiffe-identity-to-ai-agents/ |
| research | B3 | T3 | — † | — | kim | — | https://uberether.com/from-long-lived-api-keys-to-short-lived-svids/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://codingprotocols.com/tutorials/spiffe-spire-workload-identity |
| WILD | B2 | U | 2026 | url | fab | — | https://idsync.com/reports/state-of-ai-agent-identity-2026 |
| WILD | B3 | U | — † | — | fab | 10.1.10 | https://dev.to/webofmike/spiffe-workload-identity-for-ai-agents-end-to-end-8ag |
| WILD | B3 | U | — † | — | fab | — | https://www.idenhq.com/en/playbooks/spiffe-answers-who-intent-answers-why |
| WILD | B3 | U | — † | — | fab | — | https://mojoauth.com/blog/workload-identity-for-agents-spiffe-spire-vs-oauth-client-credentials |
| WILD | B3 | U | — † | — | cur | — | https://nhimg.org/faq/what-is-the-difference-between-workload-identity-and-human-identity-governance/ |
| WILD | B3 | U | — † | — | cur | — | https://oracles.cloud/workload-identity-vs-human-identity-a-zero-trust-blueprint-f |
| WILD | B3 | U | — † | — | cur fab | 10.1.10 | https://www.paloaltonetworks.com/cyberpedia/what-is-spiffe |
| WILD | B3 | U | — † | — | fab | 10.1.10 | https://sameerbhanushali.substack.com/p/spiffe-and-spire-the-workload-identity |
| WILD | B3 | U | — † | — | fab | — | https://techjacksolutions.com/ai/agentic-ai/secure/agent-identity/ |

### 10.1.2

**Q:** AuthN at each boundary — UI/API (1.1), A2A (1.5), MCP (3.5): OAuth 2.1 throughout?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | exc | kim | — | https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/authorization |
| core | B3 | T1 | 2025-03-26 | url | gpt | — | https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization |
| core | B3 | T1 | 2020-03 | exc | fab | — | https://www.ietf.org/archive/id/draft-parecki-oauth-v2-1-01.html |
| core | B3 | T1 | — † | — | fab | — | https://www.ietf.org/archive/id/draft-ietf-oauth-v2-1-14.txt |
| core | B3 | T1 | — † | — | fab | — | https://www.ietf.org/archive/id/draft-ietf-oauth-v2-1-05.txt |
| core | B3 | T1 | — † | — | kim | — | https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization |
| primary | B3 | T2 | — † | — | kim | — | https://www.cidaas.com/mcp-authorization/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/giantswarm/mcp-oauth |
| research | B2 | T3 | 2026 | url | fab | — | https://nhimg.org/articles/mcp-server-authentication-in-2026-what-practitioners-need-to-know/ |
| research | B3 | T3 | — † | — | fab kim | — | https://aembit.io/blog/mcp-oauth-2-1-pkce-and-the-future-of-ai-authorization/ |
| research | B3 | T3 | — † | — | cur kim | cursor:0.1.2 | https://nhimg.org/articles/mcp-and-a2a-use-different-auth-models-for-agentic-systems/ |
| research | B3 | T3 | — † | — | fab | — | https://vercel.com/i/mcp-server-oauth-authorization |
| WILD | B2 | U | 2026 | url | fab | — | https://baeseokjae.github.io/posts/mcp-oauth-authentication-guide-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/composiodev/mcp-oauth-21-a-complete-guide-3g91 |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/@swapnilsurdi/mcp-pa/blob/2026f08fbfc19a4c616c46220fd6f4ecf5ed0b53/src/auth/oauth21_provider.py |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/@bobmatnyc/mcp-memory-ts/blob/a04ead577ae9ed3342163e5d8266043205beccb5/docs/oauth-implementation/OAUTH_2.1_IMPLEMENTATION_SUMMARY.md |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/@portel-dev/ncp/blob/290845e3bef09f59d08c3e58660d36de9fb0b3d8/docs/OAUTH-IMPLEMENTATION.md |
| WILD | B3 | U | — † | — | fab | — | https://mojoauth.com/blog/how-mcp-authorization-actually-works-oauth-2-1-resource-servers-and-resource-indicators |

### 10.1.3

**Q:** Delegation across hops (human → agent → sub-agent → tool): token exchange (RFC 8693) or bearer pass-through? What is forbidden?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-03-27 | exc | gpt | — | https://www.ietf.org/archive/id/draft-mw-spice-actor-chain-04.html |
| core | B3 | T1 | 2020-01 | exc | kim gpt | — | https://www.rfc-editor.org/info/rfc8693/ |
| core | B3 | T1 | 2020-01 | exc | gpt | — | https://www.rfc-editor.org/rfc/rfc8693.html |
| primary | B2 | T2 | 2026-06-03 | exc | gpt | — | https://www.alibabacloud.com/help/en/idaas/eiam/user-guide/token-exchange-configuration-guide |
| primary | B3 | T2 | — † | — | kim | — | https://aws.amazon.com/blogs/machine-learning/implement-on-behalf-of-token-exchange-for-multi-tenant-agents-with-amazon-bedrock-agentcore-gateway/ |
| primary | B3 | T2 | — † | — | cur | — | https://www.cerbos.dev/blog/multi-hop-delegation-ai-agents |
| primary | B3 | T2 | — † | — | cur | — | https://www.descope.com/learn/post/oauth-token-exchange |
| primary | B3 | T2 | — † | — | fab | — | https://developer.pingidentity.com/identity-for-ai/identity/idai-token-exhange.html |
| primary | B3 | T2 | — † | — | fab | — | https://learn.microsoft.com/en-us/entra/agent-id/agent-on-behalf-of-oauth-flow |
| primary | B3 | T2 | — † | — | cur fab | — | https://workos.com/blog/oauth-multi-hop-delegation-ai-agents |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.04522 |
| research | B3 | T3 | — † | — | kim | — | https://anomity.ai/blog/ai-gateway-oauth-passthrough-mcp/ |
| research | B3 | T3 | — † | — | fab | — | https://www.gravitee.io/blog/trusted-on-behalf-of-agent-delegation-in-gravitee-4.11 |
| research | B3 | T3 | — † | — | kim | — | https://keycard.ai/blog/how-to-authorize-ai-agents-using-token-exchange-open-standards/ |
| research | B3 | T3 | — † | — | fab | — | https://nhimg.org/community/agentic-ai-and-nhis/rfc-8693-token-exchange-for-ai-agents-what-iam-teams-need/ |
| research | B3 | T3 | — † | — | kim | — | https://nitinksingh.com/posts/obo-chain-through-mcp/ |
| research | B3 | T3 | — † | — | fab | — | https://www.oleria.com/blog/on-behalf-of-identity-at-machine-speed |
| research | B3 | T3 | — † | — | kim | — | https://prateekcodes.com/multi-hop-delegation-oauth-on-behalf-of-ai-agents/ |
| WILD | B1 | U | 2026-09-03 | exc | gpt | — | https://mirrors.aliyun.com/ietf/draft-asor-wimse-agent-delegation-chain-01.html |
| WILD | B2 | U | 2026 | url | fab | — | https://anhtu.dev/ai-agent-identity-2026-authentication-and-authorization-2262 |
| WILD | B2 | U | 2026-04-11 | url | fab | — | https://zylos.ai/research/2026-04-11-agent-authentication-delegated-access-oauth-scoped-tokens |
| WILD | B3 | U | — † | — | fab | — | https://www.matthewswong.com/en/blog/ai-agent-identity-delegated-authorization/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@sauravkumarsct/oauth-delegation-for-agents-o-b-o-1e75616c2033 |
| WILD | B3 | U | — † | — | cur | — | https://nhigovernance.com/ai-agents/ai-agent-authentication.html |

### 10.1.4

**Q:** AuthZ model (RBAC / ABAC / ReBAC) served by the policy engine (2.2)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://github.com/openfga |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/affaan-m/agentshield/issues/106 |
| primary | B3 | T2 | — † | — | kim | — | https://openfga.dev/docs/use-cases/ai-agent-authorization |
| primary | B3 | T2 | — † | — | kim | — | https://openfga.dev/docs/modeling/agents/task-based-authorization |
| primary | B3 | T2 | — † | — | fab | — | https://sapl.io/guides/comparison/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.03518 |
| research | B2 | T3 | 2026-04-20 | url | fab | — | https://tianpan.co/blog/2026-04-20-rbac-ai-agents-authorization |
| research | B3 | T3 | — † | — | fab | — | https://auth0.com/blog/rebac-abac-openfga-cedar/ |
| research | B3 | T3 | — † | — | fab | — | https://authzed.com/learn/openfga-alternatives |
| research | B3 | T3 | — † | — | kim | — | https://doi.org/10.1145/3649835 |
| research | B3 | T3 | — † | — | kim | — | https://dsndaily.com/modern-authorization-models-rbac-abac-debacle/ |
| research | B3 | T3 | — † | — | fab | — | https://goteleport.com/blog/benchmarking-policy-languages/ |
| research | B3 | T3 | — † | — | kim | — | https://guptadeepak.com/guides/rbac-abac-rebac-pbac/ |
| research | B3 | T3 | — † | — | fab | — | https://nhimg.org/community/agentic-ai-and-nhis/rbac-vs-rebac-for-ai-agents-is-your-runtime-control-model-enough/ |
| research | B3 | T3 | — † | — | fab | — | https://nordicapis.com/3-core-pillars-of-ai-agent-access-control/ |
| research | B3 | T3 | — † | — | fab | — | https://www.osohq.com/learn |
| research | B3 | T3 | — † | — | fab | — | https://www.osohq.com/learn/openfga-alternatives |
| research | B3 | T3 | — † | — | fab | — | https://www.permit.io/blog/rbac-vs-rebac-for-ai-agents |
| research | B3 | T3 | — † | — | fab | — | https://www.permit.io/blog/policy-engine-showdown-opa-vs-openfga-vs-cedar |
| research | B3 | T3 | — † | — | kim | — | https://www.socratopia.app/library/security-engineering-ai-era-en/chapter-12 |
| research | B3 | T3 | — † | — | fab | — | https://zuplo.com/blog/fine-grained-authz-ai-agents |
| WILD | B2 | U | 2026-03-04 | url | gpt | — | https://github.com/DarrenStasiakDev4You/open-mercato-contrib/blob/main/.ai/specs/implemented/SPEC-060-2026-03-04-customer-identity-portal-auth.md |
| WILD | B3 | U | — † | — | fab | — | https://guptadeepak.com/ciam-compass/guides/rbac-vs-abac-vs-rebac/ |
| WILD | B3 | U | — † | — | fab | — | https://www.kiteworks.com/cybersecurity-risk-management/abac-rbac-ai-access-control/ |

### 10.1.5

**Q:** Secrets: issuance, short-lived vs static, injection into sandboxes (3.3), rotation; never in prompts — enforced where?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-10 | url | fab | — | https://docs.pwpush.com/posts/2026-08-10-Credential-Sharing-for-AI-Agents/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.docker.com/ai/sandboxes/security/credentials |
| primary | B3 | T2 | — † | — | kim | — | https://docs.docker.com/ai/sandboxes/configuration/credentials/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.iron.sh/credential-proxying/oauth-token |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/dtkav/agent-creds/ |
| primary | B3 | T2 | — † | — | fab | — | https://platform.claude.com/docs/en/managed-agents/vaults |
| research | B1 | T3 | 2026-09-09 | exc | gpt | 10.1.10 | https://www.cloudx.ai/posts/we-built-our-own-sandboxes |
| research | B1 | T3 | 2026-07-02 | url | cur | — | https://williamzujkowski.github.io/posts/2026-07-02-agentic-ai-sandbox-secret-proxying-gap/ |
| research | B3 | T3 | — † | — | cur | — | https://dreaming.press/posts/secrets-management-for-ai-agents.html |
| research | B3 | T3 | — † | — | kim | — | https://gethasp.com/guides/2026-secrets-stack-decision-matrix/ |
| research | B3 | T3 | — † | — | fab | — | https://infisical.com/blog/agent-vault-the-open-source-credential-proxy-and-vault-for-agents |
| research | B3 | T3 | — † | — | kim | — | https://infisical.com/blog/credential-brokering-for-ai-agents |
| research | B3 | T3 | — † | — | fab | — | https://nhimg.org/glossary/ai-agent-secrets-management/ |
| research | B3 | T3 | — † | — | fab | — | https://nhimg.org/community/agentic-ai-and-nhis/ai-agent-secrets-handling-what-it-means-for-iam-teams/ |
| research | B3 | T3 | — † | — | kim | — | https://onyx.app/insights/secure-agent-access-control |
| research | B3 | T3 | — † | — | cur | — | https://sandboxreview.com/posts/secrets-management-for-ai-agent-sandbox-environments |
| research | B3 | T3 | — † | — | cur | — | https://solana.garden/guides/llm-agent-secrets-credential-injection-explained/ |
| WILD | B1 | U | 2026-09-07 | url | fab | — | https://bex.co/blog/2026/09/07/keeping-secrets-out-of-ai-agents |
| WILD | B1 | U | 2026-08 | url | fab | — | https://securityboulevard.com/2026/08/secrets-management-in-the-age-of-ai-why-vaults-fall-short-and-what-replaces-them/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.codeline.co/thoughts/repo-review/2026/agent-vault-credential-proxy-for-ai-agents |
| WILD | B3 | U | — † | — | fab | — | https://ai-agent-security.com/en/best-practices/secrets-management/ |
| WILD | B3 | U | — † | — | fab | — | https://fast.io/resources/ai-agent-secrets-management/ |
| WILD | B3 | U | — † | — | fab | — | https://fast.io/resources/best-secret-management-tools-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://fast.io/resources/ai-agent-credential-vault/ |
| WILD | B3 | U | — † | — | fab | — | https://gravity.fast/blog/ai-agent-secrets-rotation/ |
| WILD | B3 | U | — † | — | fab | — | https://guptadeepak.com/secrets-management-in-the-age-of-ai-why-traditional-vaults-fall-short-and-what-comes-next/ |
| WILD | B3 | U | — † | — | fab | — | https://lushbinary.com/blog/ai-agent-security-autonomous-coding-production-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://trilogyai.substack.com/p/agent-vault-protects-secrets |

### 10.1.6

**Q:** Access control at retrieval from knowledge (8.3) and memory (4.4): is tenant isolation structural (separate index / namespace / keys per tenant) or a query-time filter alone; what is the blast radius if the filter is bypassed?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/advisories/GHSA-qc4j-qjqx-vr58 |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/Anupam2528/accessguard-rag |
| research | B1 | T3 | 2026-09-02 | url | gpt | — | https://dataplatformadvisory.com/blog/2026/09/02/multi-tenant-vector-database-cross-tenant-leakage/ |
| research | B2 | T3 | 2026 | url | fab | — | https://www.braintrust.dev/articles/best-vector-databases-for-rag-2026 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/html/2605.05287 |
| research | B2 | T3 | 2026-04-28 | url | kim | — | https://lyrie.ai/research/research/2026-04-28-spring-ai-vectorstore-filterexpression-injection |
| research | B3 | T3 | 2024-07 | url | fab | — | https://arxiv.org/pdf/2407.13193 |
| research | B3 | T3 | — † | — | fab | — | https://www.actian.com/blog/developer/how-to-build-a-multi-tenant-rag-for-customer-support/ |
| research | B3 | T3 | — † | — | kim | — | https://drel.ai/blog/multi-tenant-rag-isolation |
| research | B3 | T3 | — † | — | kim | — | https://folarin.dev/blog/building-a-multi-tenant-rag-system |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/multi-tenant-rag |
| research | B3 | T3 | — † | — | kim | — | https://raxe.ai/labs/advisories/RAXE-2026-041 |
| research | B3 | T3 | — † | — | fab | — | https://truto.one/blog/how-to-maintain-document-level-rbac-in-enterprise-rag-pipelines/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.maviklabs.com/blog/multi-tenant-rag-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://medium.com/@martinastaberger/java-rag-in-2026-the-only-guide-youll-ever-need-0e5a457663a8 |
| WILD | B3 | U | — † | — | fab | — | https://axis-intelligence.com/rag-security-statistics/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10997146 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11550773 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9460176 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11847109 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10102237 |

### 10.1.7

**Q:** Supply chain: SLSA level, SBOM format (SPDX / CycloneDX), Sigstore — applied to bundles (7.4), images (4.1), and model artifacts (weights, adapters; 10.6)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-06-25 | url | kim | — | https://openssf.org/blog/2025/06/25/an-introduction-to-the-openssf-model-signing-oms-specification/ |
| core | B3 | T1 | — † | — | kim | — | https://github.com/ossf/model-signing-spec/blob/main/README.md |
| core | B3 | T1 | — † | — | cur | — | https://slsa.dev/spec/v1.2/build-requirements |
| core | B3 | T1 | — † | — | cur | — | https://slsa.dev/spec/draft/verifying-artifacts |
| core | B3 | T1 | — † | — | fab | — | https://spdxai.github.io/publications/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/nfroze/Supply-Chain-Security-Pipeline |
| research | B2 | T3 | 2026 | url | cur | — | https://devopsboys.com/blog/software-supply-chain-security-sbom-slsa-guide-2026 |
| research | B2 | T3 | 2026-05-13 | url | gpt | — | https://blog.home301server.com.br/posts/2026-05-13-slsa-sigstore-solo-dev-supply-chain/ |
| research | B3 | T3 | — † | — | fab | — | https://www.augmentcode.com/guides/sbom-for-agent-driven-pipelines |
| research | B3 | T3 | — † | — | kim | — | https://changegamer.ai/resources/ai-supply-chain-provenance |
| research | B3 | T3 | — † | — | fab | — | https://runsafesecurity.com/blog/sbom-minimum-elements-cyclonedx-spdx/ |
| research | B3 | T3 | — † | — | kim | — | https://safeguard.sh/resources/blog/cyclonedx-ml-bom-1-7-implementation-guide-2026 |
| research | B3 | T3 | — † | — | kim | — | https://safeguard.sh/resources/blog/model-weights-as-supply-chain-artifacts-signing-and-provenance |
| research | B3 | T3 | — † | — | kim | — | https://sscsecurity.dev/book2/chapter-12/ch-12.3/ |
| WILD | B2 | U | 2026 | url | fab | — | https://appscale.blog/en/blog/supply-chain-security-ai-sbom-model-provenance-huggingface-pickle-exploits-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://safeguard.sh/resources/blog/ai-bom-spec-comparison-cyclonedx-ml-bom-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.ainformat.com/detail/1154 |
| WILD | B3 | U | — † | — | fab | — | https://architecturediagram.ai/blog/software-supply-chain-architecture |
| WILD | B3 | U | — † | — | fab | — | https://www.glacis.io/guide-ai-supply-chain-security |
| WILD | B3 | U | — † | — | fab | — | https://igotasite4that.com/tutorials/harden-cicd-pipeline-sigstore-slsa-sboms/ |
| WILD | B3 | U | — † | — | fab | — | https://www.interlynk.io/resources/cyclonedx-vs-spdx-sbom-format |
| WILD | B3 | U | — † | — | fab | — | https://safeguard.sh/resources/blog/cyclonedx-vs-spdx-which-format-for-your-program |
| WILD | B3 | U | — † | — | fab | — | https://safeguard.sh/resources/blog/spdx-3-0-ai-profile-aibom-implementation-guide |
| WILD | B3 | U | — † | — | fab | — | https://www.securegrc.io/what-is-ml-bom/ |
| WILD | B3 | U | — † | — | fab | — | https://stribog.com/blog/oss-supply-chain-security-sbom-sigstore-slsa-kubernetes |
| WILD | B3 | U | — † | — | fab | — | https://www.trantorinc.com/blog/software-supply-chain-security-sbom-slsa-engineering-teams |
| WILD | B3 | U | — † | — | cur | — | https://xdev.asia/en/blog/supply-chain-security-slsa-sbom-sigstore/ |

### 10.1.8

**Q:** Threat model: prompt-injection / tool-abuse boundary, enforced at policy (2.2), tool interface (3.5), validation (5.1).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-04-14 | url | fab | — | https://genai.owasp.org/2026/04/14/owasp-genai-exploit-round-up-report-q1-2026/ |
| core | B3 | T1 | — † | — | fab | — | https://genai.owasp.org/resources/ |
| core | B3 | T1 | — † | — | fab | — | https://genai.owasp.org/llmrisk/llm01-prompt-injection/ |
| core | B3 | T1 | — † | — | kim | — | https://genai.owasp.org/download/52117 |
| primary | B2 | T2 | 2026-03-08 | exc | gpt | — | https://github.com/Agent-Threat-Rule/agent-threat-rules/blob/main/rules/prompt-injection/ATR-2026-00005-multi-turn-injection.yaml |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-framework/blob/5eb3eb74/docs/decisions/0024-prompt-injection-defense.md |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/Agent-Threat-Rule/agent-threat-rules/blob/main/rules/prompt-injection/ATR-2026-00002-indirect-prompt-injection.yaml |
| primary | B3 | T2 | — † | — | kim | — | https://mlflow.org/articles/prompt-injection-defense/ |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.05120 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.17324 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.11868 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.18784 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.01564 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.22928 |
| research | B3 | T3 | 2025-10 | url | fab | — | https://arxiv.org/pdf/2510.08829 |
| research | B3 | T3 | 2025-07 | url | fab | — | https://arxiv.org/pdf/2507.13169 |
| research | B3 | T3 | — † | — | kim | — | https://www.deepinspect.ai/blog/owasp-top-10-agentic-applications-2026-controls-mapping |
| research | B3 | T3 | — † | — | kim | — | https://workos.com/blog/ai-agent-tool-misuse |
| WILD | B1 | U | 2026-06-11 | url | fab | — | https://www.helpnetsecurity.com/2026/06/11/owasp-prompt-injection-ai-security-failures/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/prompt-injection-attacks-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/blog/ai-agent-security-risks/ |
| WILD | B3 | U | — † | — | fab | — | https://www.practical-devsecops.com/owasp-top-10-agentic-applications/ |

### 10.1.9

**Q:** Trust tiers → runtime profiles (4.1) mapping.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://agent-sandbox.sigs.k8s.io/docs/use-cases/gvisor-isolation/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.openbox.ai/core-concepts/trust-tiers |
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/crate/axocoatl-isolation/latest/source/src/tier.rs |
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/portcullis/latest/portcullis/trust/index.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/crate/phenotype-skills/latest/source/.agileplus/specs/architecture-decisions/adr_003.yaml |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/agent-governance-toolkit/specs/AGENT-HYPERVISOR-EXECUTION-CONTROL-1.0/ |
| primary | B3 | T2 | — † | — | cur | — | https://ostk.ai/docs/isolation-tiers/ |
| research | B3 | T3 | — † | — | kim | — | https://www.agentpatternscatalog.org/patterns/risk-tiered-action-autonomy/ |
| WILD | B1 | U | 2026-08 | exc | fab | — | https://medium.com/@balajibal/agent-sandboxes-the-runtime-layer-for-enterprise-ai-agents-88f207ac5e2e |
| WILD | B1 | U | 2026-07 | url | fab | — | https://securemachinery.com/2026/07/ |
| WILD | B1 | U | 2026-07-04 | url | fab | — | https://securemachinery.com/2026/07/04/kata-containers-vs-gvisor-security-architecture-performance-full/ |
| WILD | B2 | U | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-runtimeclassname-gvisor-kata-containers/view |
| WILD | B3 | U | — † | — | fab | — | https://fast.io/resources/ai-agent-sandbox-environment/ |
| WILD | B3 | U | — † | — | fab | — | https://kubernetes.recipes/recipes/security/kata-containers-runtimeclass-kubernetes/ |
| WILD | B3 | U | — † | — | fab | — | https://www.systemshardening.com/articles/kubernetes/runtimeclass-gvisor-kata/ |

### 10.1.10

**Q:** Workload identity (10.1.1) issued per cell or job — ephemeral, revoked on sandbox teardown (3.3) — or shared across the harness fleet (3.1)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | — | https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.shield.votal.ai/agent-identity-architecture/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/NVIDIA/OpenShell/issues/1665 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.17909 |
| research | B3 | T3 | — † | — | fab | — | https://aembit.io/blog/attestation-based-identity-hardware-cloud-security/ |
| research | B3 | T3 | — † | — | kim | — | https://www.agentpatternscatalog.org/patterns/ephemeral-agent-identity/ |
| research | B3 | T3 | — † | — | kim | — | https://www.descope.com/blog/post/ai-agent-credential-management |
| research | B3 | T3 | — † | — | kim | — | https://github.com/devonartis/AI-Security-Blueprints/blob/main/patterns/ephemeral-agent-credentialing/versions/v1.3.md |
| research | B3 | T3 | — † | — | fab | — | https://goteleport.com/blog/spiffe-workload-identity/ |
| research | B3 | T3 | — † | — | kim | — | https://mahasbini.org/papers/01-agents-not-service-accounts/ |
| research | B3 | T3 | — † | — | fab | — | https://nhimg.org/glossary/spiffe-svid/ |
| research | B3 | T3 | — † | — | fab | — | https://www.solo.io/blog/spire-attestable-workload-identity |
| research | B3 | T3 | — † | — | kim | — | https://workos.com/blog/ai-agent-credentials |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/kanywst/spiffespire-deep-dive-a5p |
| WILD | B3 | U | — † | — | fab | — | https://evertrust.io/guide/agentic-identity-spiffe/ |
| WILD | B3 | U | — † | — | fab | — | https://petronellatech.com/blog/machine-identity-is-the-new-perimeter-mtls-spiffe-for-zero-trust/ |
| WILD | B3 | U | — † | — | fab | — | https://stribog.com/blog/spiffe-spire-zero-trust-workload-identity-kubernetes-mtls |
| WILD | B3 | U | — † | — | fab | — | https://www.systemshardening.com/articles/cross-cutting/spiffe-spire-workload-identity/ |

### 10.2.1

**Q:** Policy-as-code location and language (2.2); single source of truth?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/OWASP/DevSecOpsGuideline/blob/master/current-version/3-Governance/3-1-Compliance-Auditing/3-1-2-Policy-as-code.md |
| primary | B3 | T2 | — † | — | kim | — | https://docs.cedarpolicy.com/overview/patterns.html |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/observatorium/api/pull/793 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/cedar-policy/rfcs/pull/101 |
| primary | B3 | T2 | — † | — | cur | — | https://learn.microsoft.com/en-us/azure/governance/policy/concepts/policy-as-code |
| primary | B3 | T2 | — † | — | kim | — | https://microsoft.github.io/agent-governance-toolkit/adr/0029-policy-distribution-and-registries/ |
| primary | B3 | T2 | — † | — | cur | — | https://www.pulumi.com/what-is/what-is-policy-as-code/ |
| primary | B3 | T2 | — † | — | kim | — | https://pypi.org/project/agentpolicypack/ |
| research | B1 | T3 | 2026-06-17 | url | kim | — | https://www.cncf.io/blog/2026/06/17/why-cloud-native-belongs-at-the-heart-of-agentic-ai-lessons-from-building-a-multi-agent-security-platform-on-kubernetes/ |
| research | B2 | T3 | 2026-04 | exc | fab | — | https://www.researchgate.net/publication/404400476_Policy_as_Code_in_GitOps_Implementing_Compliance_Automation_with_OPA_and_Kyverno |
| research | B2 | T3 | 2026-04-25 | url | fab | — | https://tianpan.co/blog/2026-04-25-policy-as-code-agent-permissions-opa-rego |
| research | B3 | T3 | — † | — | kim | — | https://johal.in/retrospective-using-opa-065-policy-enforcement-across-100 |
| research | B3 | T3 | — † | — | fab | — | https://www.osohq.com/learn/opa-vs-cedar-vs-zanzibar |
| research | B3 | T3 | — † | — | fab | — | https://www.permit.io/blog/opa-vs-cedar |
| research | B3 | T3 | — † | — | cur | — | https://www.plural.sh/blog/kubernetes-policy-as-code-governance/ |
| WILD | B3 | U | — † | — | cur | — | https://booleandata.ai/policy-as-code-in-snowflake-automating-governance-at-scale/ |
| WILD | B3 | U | — † | — | fab | — | https://www.cybersrely.com/opa-vs-cedar-ship-policy-as-code/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@debghosal01/opa-gitops-enhancing-compliance-security-and-automation-for-platform-teams-426bc53ce9c4 |
| WILD | B3 | U | — † | — | fab | — | https://scalr.com/learning-center/enforcing-policy-as-code-in-terraform-a-comprehensive-guide |
| WILD | B3 | U | — † | — | fab | — | https://spacelift.io/blog/policy-as-code-tools |
| WILD | B3 | U | — † | — | fab | — | https://www.strongdm.com/cedar-policy-language |
| WILD | B3 | U | — † | — | fab | — | https://www.systemshardening.com/articles/cross-cutting/policy-as-code-at-scale/ |
| WILD | B3 | U | — † | — | fab | — | https://zop.dev/resources/blogs/opa-vs-cedar-when-policy-as-code-hits-500-accounts |

### 10.2.2

**Q:** Audit event schema (CloudEvents envelope, OCSF fields?) and immutability; covers policy decisions (2.2), admissions (5.2), promotions (7.4).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-09-04 | exc | fab gpt | — | https://github.com/ocsf/ocsf-schema |
| core | B3 | T1 | — † | — | kim | — | https://aos.owasp.org/spec/trace/extend_ocsf/ |
| core | B3 | T1 | — † | — | cur kim | — | https://github.com/ocsf/ocsf-schema/releases/tag/1.9.0 |
| core | B3 | T1 | — † | — | cur kim | — | https://github.com/ocsf/ocsf-schema/pull/1661 |
| core | B3 | T1 | — † | — | cur | — | https://github.com/ocsf/ocsf-schema/blob/main/CHANGELOG.md |
| core | B3 | T1 | — † | — | fab | — | https://github.com/ocsf |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/ocsf/ocsf-docs/blob/main/overview/understanding-ocsf.md |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/ocsf/ocsf-schema/blob/main/events/base_event.json |
| core | B3 | T1 | — † | — | kim | — | https://www.ietf.org/archive/id/draft-sharif-agent-audit-trail-01.txt |
| primary | B1 | T2 | 2026-09-08 | exc | fab | — | https://tenzir.com/changelog/tenzir/v6.16.0/ |
| primary | B3 | T2 | — † | — | fab | — | https://community.sailpoint.com/t5/Identity-Security-Cloud-Wiki/SailPoint-AuditEvent-Integration-for-Amazon-Security-Lake-Setup/ta-p/241725 |
| primary | B3 | T2 | — † | — | fab gpt | — | https://developer.adobe.com/events/docs/guides/using/admin-audit-logs/format |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/security-lake/latest/userguide/open-cybersecurity-schema-framework.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.confluent.io/cloud/current/monitoring/audit-logging/audit-log-schema.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.openg2p.org/platform/platform-services/audit-manager/functional-specifications |
| primary | B3 | T2 | — † | — | fab | — | https://docs.oracle.com/en-us/iaas/tools/terraform-provider-oci/latest/docs/d/audit_events.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.redpanda.com/current/manage/audit-logging/audit-log-samples/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/B5Secure/ocsf-authority |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ai-identity/forensic-audit-trail-spec |
| primary | B3 | T2 | — † | — | fab | — | https://gitlab.com/gitlab-org/gitlab/-/issues/406558 |
| primary | B3 | T2 | — † | — | fab | — | https://www.mongodb.com/docs/manual/reference/audit-message/ocsf/ |
| primary | B3 | T2 | — † | — | fab | — | https://packs.cribl.io/packs/azure-audit-log-ocsf |
| primary | B3 | T2 | — † | — | gpt | — | https://pkg.go.dev/github.com/ocsf/ocsf-toolkit%40v0.8.0/eventschema |
| research | B3 | T3 | — † | — | gpt | — | https://docs.aws.amazon.com/appfabric/latest/adminguide/ocsf-schema.html |
| research | B3 | T3 | — † | — | gpt | — | https://docs.cloud.google.com/eventarc/docs/cloudevents-json |
| research | B3 | T3 | — † | — | gpt | — | https://docs.cloud.google.com/eventarc/docs/cloudevents?hl=en |
| WILD | B2 | U | 2026-02-16 | url | fab | — | https://oneuptime.com/blog/post/2026-02-16-how-to-use-cloudevents-schema-with-azure-event-grid/view |
| WILD | B3 | U | — † | — | fab | — | https://www.apriorit.com/dev-blog/open-cybersecurity-schema-framework-implementation-guide |
| WILD | B3 | U | — † | — | fab | — | https://www.datadoghq.com/knowledge-center/ocsf/ |
| WILD | B3 | U | — † | — | fab | — | https://www.deepwatch.com/glossary/open-cybersecurity-schema-framework-ocsf/ |
| WILD | B3 | U | — † | — | fab | — | https://fleak.ai/blog/ocsf-mapping |
| WILD | B3 | U | — † | — | fab | — | https://hex.pm/packages/ocsf/audit-logs |

### 10.2.3

**Q:** Decision point (2.2) vs enforcement points (2.1, 3.5, 5.1, 5.2) — listed and owned.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026 | url | fab | — | https://openid.net/authzen-at-identiverse-2026-authorization-in-the-agent-era/ |
| core | B3 | T1 | — † | — | cur kim | cursor:0.2.3 | https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-207.pdf |
| core | B3 | T1 | — † | — | kim | — | https://pages.nist.gov/zero-trust-architecture/glossary.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/agent-governance-toolkit/blob/main/docs/tutorials/07-mcp-security-gateway.md |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.29142 |
| research | B3 | T3 | 2025-10 | url | fab | — | https://arxiv.org/pdf/2510.25819 |
| research | B3 | T3 | — † | — | fab | — | https://axiomatics.com/blog/enforcement-strategies-when-peps-not-enough |
| research | B3 | T3 | — † | — | kim | — | https://devsecopsschool.com/blog/pdp/ |
| research | B3 | T3 | — † | — | kim | — | https://www.empowerid.com/platform/mcp-gateway |
| research | B3 | T3 | — † | — | fab | — | https://www.osohq.com/authorization-glossary/policy-enforcement-point-pep |
| research | B3 | T3 | — † | — | fab | — | https://techcommunity.microsoft.com/blog/microsoft-security-blog/authorization-and-governance-for-ai-agents-runtime-authorization-beyond-identity/4509161 |
| research | B3 | T3 | — † | — | kim | — | https://zero-trust-insider.contentwave.net/article/central-pdp-vs-distributed-pep-zerotrust-trade-offs-for-global-it |
| WILD | B2 | U | 2026 | url | fab | — | https://andrewdoering.org/blog/2026/authzen-shared-signals-framework-part-1-fundamentals/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8498959 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12395549 |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10348739 |
| WILD | B3 | U | — † | — | fab | — | https://www.wikimolt.org/page/Policy%20Enforcement%20Point%20(PEP)/revision/3253 |

### 10.2.4

**Q:** Target compliance frameworks (SOC 2, ISO 27001, EU AI Act, none yet).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | — | https://artificialintelligenceact.eu/high-level-summary/ |
| research | B2 | T3 | 2026 | url | fab kim | — | https://www.kosmoy.com/resources/blog/best-ai-compliance-platforms-2026/ |
| research | B2 | T3 | 2026-06-04 | url | cur | — | https://beancount.io/blog/2026/06/04/eu-ai-act-compliance-us-saas-foundation-model-ai-agent-companies-non-eu-provider-article-22-authorized-representative-gpai-code-of-practice-august-2026-deadline-guide |
| research | B3 | T3 | — † | — | cur | — | https://www.adaptivesecurity.com/blog/ai-compliance-management-the-complete-guide-6afe7 |
| research | B3 | T3 | — † | — | kim | — | https://www.arthur.ai/blog/eu-ai-act-compliance-for-ai-agents |
| research | B3 | T3 | — † | — | cur | — | https://elevateconsult.com/insights/ai-governance-frameworks-compared-matching-nist-eu-ai-act-and-iso-42001-to-your-use-case/ |
| research | B3 | T3 | — † | — | cur | — | https://governance.aicareer.pro/blog/ai-governance-controls-mega-map |
| research | B3 | T3 | — † | — | fab | — | https://labs.cloudsecurityalliance.org/research/csa-research-note-eu-ai-act-high-risk-compliance-deadline-20/ |
| research | B3 | T3 | — † | — | kim | — | https://www.praxikon.com/en/posts/agentic-ai-governance |
| research | B3 | T3 | — † | — | kim | — | https://www.securisea.com/resources/iso-42001-certification-requirements-what-organizations-should-expect |
| research | B3 | T3 | — † | — | kim | — | https://specswriter.com/knowledge/what_is_iso_42001_agentic_ai_certification_and_how_do_companies_get_certified_for_autonomous_ai_agents.php |
| WILD | B2 | U | 2026 | url | fab | — | https://www.aiacto.eu/en/blog/ai-act-what-changes-august-2-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://aiagentrank.io/blog/ai-agent-compliance-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.digitalapplied.com/blog/ai-agent-governance-policy-compliance-2026 |
| WILD | B2 | U | 2026 | url | cur | — | https://www.knowlee.ai/blog/iso-42001-vs-soc2-vs-iso-27001-comparison |
| WILD | B2 | U | 2026 | url | fab | — | https://www.knowlee.ai/blog/ai-security-compliance-framework-2026 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.legalnodes.com/article/eu-ai-act-2026-updates-compliance-requirements-and-business-risks |
| WILD | B2 | U | 2026 | url | fab | — | https://www.mckennaconsultants.com/eu-ai-act-high-risk-compliance-a-technical-readiness-guide-for-august-2026/ |
| WILD | B2 | U | 2026 | url | fab | — | https://secureprivacy.ai/blog/eu-ai-act-2026-compliance |
| WILD | B2 | U | 2026-04 | url | fab | — | https://www.hklaw.com/en/insights/publications/2026/04/us-companies-face-eu-ai-acts-possible-august-2026-compliance-deadline |
| WILD | B3 | U | — † | — | fab | — | https://cloud-captains.com/en/article/the-eu-ai-act-compliance-guide-for-global-businesses |
| WILD | B3 | U | — † | — | fab | — | https://omnithium.ai/blog/ai-agent-compliance-soc2-iso-eu-ai-act.html |
| WILD | B3 | U | — † | — | fab | — | https://www.vynoxsecurity.com/feeds/service/ai-security-compliance |

### 10.2.5

**Q:** Change control for policy, models, prompts, tools — approval evidence recorded where?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.thalian.ai/audit-log-chain-of-custody/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/responsibleai/ASSERT/blob/c26c8425/examples/change_control_agent/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/berkayturanci/keel/blob/main/docs/keel/evidence.md |
| research | B3 | T3 | — † | — | cur | — | https://ai-rng.com/change-control-for-prompts-tools-and-policies-versioning-the-invisible-code/ |
| research | B3 | T3 | — † | — | kim | — | https://aigovernance.com/controls/ai-model-change-documentation |
| research | B3 | T3 | — † | — | kim | — | https://aiprompts.cloud/audit-friendly-prompt-versioning-for-teams-working-on-safety |
| research | B3 | T3 | — † | — | cur | — | https://clarisec.in/ai-model-prompt-change-management-guide/ |
| research | B3 | T3 | — † | — | cur | — | https://www.compelframework.org/articles/template-prompt-registry-entry-and-test-plan |
| research | B3 | T3 | — † | — | cur | — | https://www.compelframework.org/articles/prompt-lifecycle-governance |
| WILD | B2 | U | 2026 | url | fab | — | https://alinajafzadeh.at/blog/ai-change-control-model-prompt-agent-updates-austria-2026.html |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/best-prompt-governance-platforms-for-enterprise-ai-in-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.truefoundry.com/blog/ai-audit-checklist |
| WILD | B2 | U | 2026 | url | fab | — | https://trussed.ai/resources/eu-ai-act-enforcement-august-2026-guide |
| WILD | B2 | U | 2026-06 | exc | fab | — | https://www.openlayer.com/blog/ai-model-audit-complete-guide |
| WILD | B2 | U | 2026-03 | exc | fab | — | https://medium.com/@aisquarecommunity/prompt-governance-scale-versioning-access-and-audits-c76b58a166f1 |
| WILD | B3 | U | — † | — | fab | — | https://www.floqast.com/blog/what-ai-audit-controls-actually-look-like |
| WILD | B3 | U | — † | — | fab | — | https://intuitionlabs.ai/articles/changing-ai-models-validated-workflows-regression-testing |
| WILD | B3 | U | — † | — | fab | — | https://promptbuilder.cc/blog/ai-governance-and-compliance |
| WILD | B3 | U | — † | — | fab | — | https://www.solytics-partners.com/resources/blogs/prompt-governance |

### 10.2.6

**Q:** Record-keeping: does the audit log (10.2.2) meet the minimum retention required for high-risk AI record-keeping (e.g. EU AI Act Art. 12 / 19), independent of telemetry retention (6.1.4)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-27 | url | gpt | — | https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng |
| core | B3 | T1 | — † | — | fab | — | https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-12 |
| core | B3 | T1 | — † | — | fab kim | — | https://artificialintelligenceact.eu/article/12/ |
| core | B3 | T1 | — † | — | fab | — | https://artificialintelligenceact.eu/article/19/ |
| research | B3 | T3 | — † | — | kim | — | https://aiactstack.com/article/art-19 |
| research | B3 | T3 | — † | — | fab kim | — | https://www.deepinspect.ai/blog/eu-ai-act-article-19-logs |
| research | B3 | T3 | — † | — | fab kim | — | https://www.legalithm.com/en/blog/eu-ai-act-log-retention-record-keeping-6-months |
| research | B3 | T3 | — † | — | fab kim | — | https://predictionguard.com/blog/eu-ai-act-compliance-audit-log-what-regulators-expect-and-how-to-document-it |
| WILD | B3 | U | — † | — | fab | — | https://www.aiactblog.nl/en/ai-act/artikel/19 |
| WILD | B3 | U | — † | — | fab | — | https://www.aiexponent.com/eu-ai-act/article-19 |
| WILD | B3 | U | — † | — | fab | — | https://www.artificial-intelligence-act.com/Artificial_Intelligence_Act_Article_12.html |
| WILD | B3 | U | — † | — | fab | — | https://certifieddata.io/eu-ai-act/article-12-record-keeping |
| WILD | B3 | U | — † | — | fab | — | https://commonlawyer.substack.com/p/an-ai-act-article-a-day-19-log-retention |
| WILD | B3 | U | — † | — | fab | — | https://www.firetail.ai/blog/article-12-and-the-logging-mandate-what-the-eu-ai-act-actually-requires |
| WILD | B3 | U | — † | — | fab | — | https://www.isms.online/iso-42001/eu-ai-act/article-12/ |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@axel.schwanke/compliance-under-the-eu-ai-act-best-practices-for-monitoring-and-logging-e098a3d6fe9d |
| WILD | B3 | U | — † | — | fab | — | https://mickai.co.uk/articles/how-long-must-you-keep-ai-decision-logs-under-eu-rules |
| WILD | B3 | U | — † | — | fab | — | https://ovidiusuciu.com/eu-ai-act/eu-ai-act-article-19-automatically-generated-logs/ |
| WILD | B3 | U | — † | — | fab | — | https://practical-ai-act.eu/latest/conformity/record-keeping/ |
| WILD | B3 | U | — † | — | fab | — | https://truescreen.io/insights/ai-act-record-keeping-requirements/ |

### 10.3.1

**Q:** Exactly one owner per failure class: retries / timeouts / idempotency in workflow (2.4), harness (3.1), or gateway (3.2)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://airflow.apache.org/docs/apache-airflow-providers-common-ai/stable/retry_policies.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/encyclopedia/retry-policies |
| primary | B3 | T2 | — † | — | fab | — | https://docs.temporal.io/ai/cookbook/http-retry-enhancement-python |
| primary | B3 | T2 | — † | — | kim | — | https://go.temporal.io/platform-hub/ai-engineering/ai-reference-architecture |
| primary | B3 | T2 | — † | — | kim | — | https://www.xgrid.co/resources/ai-workflow-orchestration/ |
| research | B2 | T3 | 2026-05-02 | url | fab | — | https://tianpan.co/blog/2026-05-02-tail-tolerant-retry-policy-llm-gateway-latency-cliff |
| research | B3 | T3 | — † | — | fab | — | https://www.augmentcode.com/guides/async-ai-agent-workflows |
| research | B3 | T3 | — † | — | kim | — | https://github.com/stevekinney/stevekinney.net/blob/main/writing/ai-gateway-durable-workflows.md |
| research | B3 | T3 | — † | — | fab | — | https://www.inngest.com/blog/durable-execution-key-to-harnessing-ai-agents |
| research | B3 | T3 | — † | — | kim | — | https://pragmaticstack.in/designing-agentic-workflow-engine |
| research | B3 | T3 | — † | — | kim | — | https://www.requesty.ai/blog/agent-harness-why-your-llm-gateway-is-the-backbone-of-production-agents |
| WILD | B1 | U | 2026-08 | exc | fab | — | https://blog.wahab2.com/api-architecture-designing-apis-for-failure-retries-idempotency-timeouts-and-graceful-ccba1195cfde?gi=a03578ba7c8b |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/glossary/retry-strategy/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.spheron.network/blog/ai-agent-workflow-orchestration-temporal-inngest-restate-gpu-cloud/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/hosseinhezami/what-happens-when-an-ai-agent-runs-longer-than-your-http-request-288o |
| WILD | B3 | U | — † | — | fab | — | https://www.meritshot.com/blog/bde-retry-logic-doubles-openai-bill |
| WILD | B3 | U | — † | — | fab | — | https://orca.security/resources/blog/agentic-workflows/ |

### 10.3.2

**Q:** Idempotency key convention across entry points (1.x) and tool calls (3.5).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-10-15 | exc | fab | — | https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-07 |
| core | B3 | T1 | — † | — | cur | — | https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Idempotency-Key |
| core | B3 | T1 | — † | — | kim | — | https://github.com/modelcontextprotocol/modelcontextprotocol/pull/3182 |
| core | B3 | T1 | — † | — | fab | — | https://www.ietf.org/archive/id/draft-ietf-httpapi-idempotency-key-header-01.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.stripe.com/api/idempotent_requests |
| research | B3 | T3 | — † | — | fab | — | https://blogs.oracle.com/developers/the-agent-communication-matrix-when-mcp-a2a-and-plain-rest-each-win |
| research | B3 | T3 | — † | — | cur kim | — | https://dev.to/gabrielanhaia/idempotent-tool-calls-the-retry-safety-net-agents-forget-5cg8 |
| research | B3 | T3 | — † | — | cur kim | — | https://www.pontil.com/blog/api-idempotency-for-ai-agents-a-practical-guide-to-safe |
| research | B3 | T3 | — † | — | kim | — | https://prufa.dev/blog/engineering/idempotency-keys-for-ai-agents/ |
| research | B3 | T3 | — † | — | kim | — | https://replyant.com/lab/a2a-protocol-v1-production/ |
| WILD | B2 | U | 2026 | url | fab | — | https://www.elegantsoftwaresolutions.com/blog/mcp-2026-agent-to-agent-communication-guide |
| WILD | B3 | U | — † | — | fab | — | https://www.channel.tel/blog/idempotent-tool-calls-agent-retry-safety |
| WILD | B3 | U | — † | — | fab | — | https://glama.ai/mcp/servers/krish-shahh/mcp-idempotent |
| WILD | B3 | U | — † | — | fab | — | https://greenbytes.de/tech/specs/draft-ietf-httpapi-idempotency-key-header-latest.html |
| WILD | B3 | U | — † | — | fab | — | https://www.motomtech.com/blog-post/ai-agent-retries-idempotency-tool-failures/ |

### 10.3.3

**Q:** Delivery semantics per hop (1.3, 2.4, 3.5): at-least-once vs exactly-once; where is dedup?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://cwiki.apache.org/confluence/spaces/KAFKA/pages/66854913/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging |
| primary | B3 | T2 | — † | — | cur | — | https://developer.confluent.io/courses/architecture/transactions/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.axonops.com/data-platforms/kafka/concepts/delivery-semantics/ |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/azure/architecture/patterns/idempotent-consumer |
| primary | B3 | T2 | — † | — | fab | — | https://nats.io/blog/new-per-subject-discard-policy/ |
| research | B2 | T3 | 2026-06-02 | url | kim | — | https://zylos.ai/research/2026-06-02-transactional-outbox-pattern-ai-agent-coordination/ |
| research | B2 | T3 | 2026-04-27 | url | kim | — | https://zylos.ai/research/2026-04-27-message-delivery-semantics-in-flight-recovery-agent-runtimes/ |
| research | B3 | T3 | 2025-12 | url | fab | — | https://arxiv.org/pdf/2512.16146 |
| research | B3 | T3 | 2024-10 | url | fab | — | https://arxiv.org/pdf/2410.15533 |
| research | B3 | T3 | 2021-06 | url | fab | — | https://arxiv.org/pdf/2106.00583 |
| research | B3 | T3 | — † | — | kim | — | https://airbyte.com/blog/designing-idempotent-write-operations |
| research | B3 | T3 | — † | — | kim | — | https://hld.handbook.academy/curriculum/distributed-systems-theory/idempotency-exactly-once/ |
| research | B3 | T3 | — † | — | cur | — | https://petascalelabs.com/blog/kafka-exactly-once-idempotence-transactions-read-committed |
| research | B3 | T3 | — † | — | kim | — | https://sujeet.pro/articles/exactly-once-delivery |
| WILD | B2 | U | 2026-01-30 | url | fab | — | https://oneuptime.com/blog/post/2026-01-30-event-delivery-semantics/view |
| WILD | B2 | U | 2026-01-26 | url | fab | — | https://oneuptime.com/blog/post/2026-01-26-nats-jetstream-persistence/view |
| WILD | B3 | U | 2025-11-06 | url | fab | — | https://blog.vitalvas.com/post/2025/11/06/kafka-vs-nats-jetstream/ |
| WILD | B3 | U | — † | — | fab | — | https://www.conduktor.io/glossary/exactly-once-semantics-in-kafka |
| WILD | B3 | U | — † | — | fab | — | https://estuary.dev/blog/exactly-once-delivery/ |
| WILD | B3 | U | — † | — | fab | — | https://i-flow.io/en/ressources/nats-vs-kafka-comparison-for-the-uns/ |
| WILD | B3 | U | — † | — | fab | — | https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12061608 |
| WILD | B3 | U | — † | — | fab | — | https://www.linkedin.com/pulse/event-driven-data-architecture-patterns-exactly-once-delivery-singh |
| WILD | B3 | U | — † | — | fab | — | https://luismori.dev/article/nats-jetstream-persistence-streams-consumers/ |
| WILD | B3 | U | — † | — | cur | — | https://medium.com/threadsafe/exactly-once-processing-across-kafka-and-databases-using-kafka-transactions-idempotent-writes-09fe1f75bdab |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@sendoamoronta/achieving-exactly-once-file-processing-with-google-cloud-functions-and-cloud-storage-a9ef4a4521d6 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@hadiyolworld007/nats-jetstream-playbook-exactly-once-minus-the-bloat-02fd9d5a051c |
| WILD | B3 | U | — † | — | fab | — | https://repost.aws/questions/QUEi1t0HGeTVakJB2VKl-Q3g/eventbridge-duplicate-events-due-to-at-least-once-delivery |
| WILD | B3 | U | — † | — | fab | — | https://semicolony.dev/vs/nats-vs-kafka |
| WILD | B3 | U | — † | — | fab | — | https://timderzhavets.com/blog/nats-jetstream-vs-kafka-choosing-the-right-persistent/ |

### 10.3.4

**Q:** SLOs per layer and per entry type; error budget owner.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://sre.google/workbook/implementing-slos/ |
| primary | B3 | T2 | — † | — | cur | — | https://hld.handbook.academy/curriculum/reliability-and-operations/sli-slo-sla-error-budgets/ |
| research | B1 | T3 | 2026-08-16 | url | kim | — | https://devtocash.com/blog/2026-08-16-error-budget-ai-agent-slo-burn-rate |
| research | B2 | T3 | 2026 | url | cur | — | https://openobserve.ai/blog/set-meaningful-slos |
| research | B2 | T3 | 2026-04-23 | url | kim | — | https://tianpan.co/blog/2026-04-23-agent-latency-budgets-trees-not-lines |
| research | B2 | T3 | 2026-04-15 | url | kim | — | https://tianpan.co/blog/2026/04/15/latency-budgets-ai-features |
| research | B2 | T3 | 2026-03-13 | url | cur | — | https://www.youngju.dev/blog/observability/2026-03-13-sli-slo-error-budget-reliability-engineering-guide.en |
| research | B3 | T3 | — † | — | kim | — | https://ai-rng.com/reliability-slas-and-service-ownership-boundaries/ |
| research | B3 | T3 | — † | — | kim | — | https://cloudai.pt/three-slo-layers-for-ai-reliability-systems-in-2026/ |
| research | B3 | T3 | — † | — | cur | — | https://codably.dev/devops/service-level-objectives-a-developers-guide-to-slos |
| research | B3 | T3 | — † | — | fab | — | https://www.datadoghq.com/state-of-ai-engineering/ |
| research | B3 | T3 | — † | — | kim | — | https://sreekarreddy.com/ai-posts/operating-agents-production |
| research | B3 | T3 | — † | — | fab kim | — | https://techcommunity.microsoft.com/blog/linuxandopensourceblog/applying-site-reliability-engineering-to-autonomous-ai-agents/4521357 |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/ai-agent-error-budget-sre-reliability-autonomous-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://cubeapm.com/blog/best-slo-monitoring-tools/ |
| WILD | B2 | U | 2026 | url | fab | — | https://futureagi.com/blog/ai-agent-reliability-metrics-2026/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://noopsschool.com/blog/slo/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://performance.qa/blog/slo-sli-error-budgets-guide/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://sreschool.com/blog/error-budget/ |
| WILD | B2 | U | 2026 | url | fab | — | https://techbytes.app/posts/sre-handbook-2026-slos-error-budgets-incident-runbooks/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.xopsschool.com/tutorials/error-budget/ |
| WILD | B3 | U | — † | — | fab | — | https://backendbytes.com/articles/sre-slos-slis-error-budgets/ |
| WILD | B3 | U | — † | — | fab | — | https://www.velsof.com/ai-automation/ai-agent-reliability-engineering-slo-patterns/ |

### 10.3.5

**Q:** Circuit breaking / backpressure — gateway (3.2), mesh, or code?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-07 | age | cur kim | cursor:3.2.4 | https://agentgateway.dev/docs/standalone/latest/configuration/resiliency/rate-limits/ |
| primary | B3 | T2 | — † | — | fab | — | https://aigateway.envoyproxy.io/release-notes/ |
| primary | B3 | T2 | — † | — | kim | — | https://aigateway.envoyproxy.io/docs/0.2/capabilities/usage-based-ratelimiting/ |
| primary | B3 | T2 | — † | — | fab | — | https://ambientmesh.io/docs/resilience/circuit-breakers/ |
| primary | B3 | T2 | — † | — | cur | — | https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking.html |
| primary | B3 | T2 | — † | — | kim | — | https://gateway.envoyproxy.io/latest/tasks/traffic/circuit-breaker/ |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/envoyproxy/gateway/releases |
| primary | B3 | T2 | — † | — | cur | — | https://istio.io/latest/docs/reference/config/networking/destination-rule/ |
| primary | B3 | T2 | — † | — | fab | — | https://kgateway.dev/docs/envoy/latest/reference/release-notes/ |
| research | B2 | T3 | 2026-04-27 | url | kim | — | https://tianpan.co/blog/2026/04/27/internal-llm-gateway-service-mesh-pattern |
| research | B2 | T3 | 2026-04-15 | url | fab | — | https://tianpan.co/blog/2026-04-15-backpressure-llm-pipelines |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.01548 |
| research | B2 | T3 | 2026-02-25 | url | kim | — | https://zylos.ai/research/2026-02-25-rate-limiting-backpressure-ai-agent-apis/ |
| research | B3 | T3 | — † | — | kim | — | https://designgurus.substack.com/p/api-gateway-vs-service-mesh-vs-sidecar |
| research | B3 | T3 | — † | — | cur | — | https://www.request-routing.com/api-gateway-fundamentals-architecture/api-gateway-vs-service-mesh/ |
| research | B3 | T3 | — † | — | cur | — | https://www.systemoverflow.com/learn/resilience-patterns/circuit-breaker/circuit-breaker-placement-client-side-service-mesh-or-gateway |
| WILD | B2 | U | 2026 | url | fab | 10.6.3 10.6.4 10.6.5 | https://www.braintrust.dev/articles/best-llm-routers-2026 |
| WILD | B2 | U | 2026 | url | fab | 10.6.3 | https://www.digitalapplied.com/blog/llm-gateway-architecture-2026-engineering-reference |
| WILD | B2 | U | 2026 | url | fab | — | https://www.getmaxim.ai/articles/top-5-llm-failover-routing-gateways-in-2026/ |
| WILD | B2 | U | 2026 | url | fab | 10.6.5 | https://jobsbyculture.com/blog/llm-gateway-design-guide-2026 |
| WILD | B2 | U | 2026-06-05 | url | fab | — | https://rawkode.academy/news/2026-06-05-envoy-istio-nccl |
| WILD | B2 | U | 2026-04-30 | url | fab | — | https://blog.none.at/blog/2026/2026-04-30-istio-vs-envoy-gateway/ |
| WILD | B2 | U | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-api-gateway-circuit-breaking-envoy/view |
| WILD | B2 | U | 2026-01-27 | url | fab | — | https://oneuptime.com/blog/post/2026-01-27-envoy-circuit-breaker/view |
| WILD | B3 | U | — † | — | cur | — | https://codinizer.com/circuit-breaker-pattern-microservices/ |
| WILD | B3 | U | — † | — | fab | — | https://www.getmaxim.ai/articles/retries-fallbacks-and-circuit-breakers-in-llm-apps-a-production-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://www.istioworkshop.io/09-traffic-management/06-circuit-breaker/ |

### 10.3.6

**Q:** Fault-injection plan: sandbox kill (3.3), provider outage (3.2), queue loss (1.3).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-08-06 | url | fab | — | https://www.cncf.io/blog/2026/08/06/litmuschaos-q1-q2-2026-update-community-contributions-and-project-progress/ |
| primary | B3 | T2 | — † | — | cur | — | https://developer.harness.io/docs/chaos-engineering/faults/chaos-faults/azure/azure-service-bus-queue-state-change/ |
| primary | B3 | T2 | — † | — | kim | — | https://faultkit.dev/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/reaatech/agent-chaos |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Blakeinstein/agentbreak |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/IntelligentDDS/AgentChaos |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/arielshad/balagan-agent |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ExordexLabs/khaos-sdk |
| research | B1 | T3 | 2026-08 | url | fab | — | https://arxiv.org/html/2608.06790 |
| research | B1 | T3 | 2026-08 | url | fab | — | https://arxiv.org/abs/2608.06790 |
| research | B1 | T3 | 2026-08-01 | exc | kim | — | https://arxiv.org/html/2608.06790v1 |
| research | B2 | T3 | 2026-04-12 | url | fab | — | https://tianpan.co/blog/2026-04-12-chaos-engineering-ai-agents-injecting-failures-before-production |
| research | B3 | T3 | — † | — | cur | — | https://multigrid.ai/learn/chaos-test-ai-provider |
| WILD | B2 | U | 2026 | url | fab | — | https://www.buildmvpfast.com/blog/agentic-chaos-engineering-ai-fuzzing-bug-hunting-security-2026 |
| WILD | B2 | U | 2026 | exc | fab | — | https://kubernetes.qa/blog/chaos-mesh-vs-litmus/ |
| WILD | B2 | U | 2026 | url | fab | — | https://reintech.io/blog/litmuschaos-vs-chaos-mesh-kubernetes-chaos-tool-comparison-2026 |
| WILD | B2 | U | 2026-02 | url | fab | — | https://www.emergentmind.com/papers/2602.20021 |
| WILD | B2 | U | 2026-02-20 | url | fab | — | https://oneuptime.com/blog/post/2026-02-20-chaos-engineering-kubernetes/view |
| WILD | B3 | U | — † | — | fab | — | https://fast.io/resources/ai-agent-chaos-engineering/ |
| WILD | B3 | U | — † | — | cur | — | https://reintech.io/blog/testing-azure-aks-resilience-chaos-engineering |
| WILD | B3 | U | — † | — | fab | — | https://stresstest.qa/blog/litmus-vs-chaos-mesh/ |
| WILD | B3 | U | — † | — | fab | — | https://stribog.com/blog/litmuschaos-chaos-mesh-resilience-verification-audit-evidence |
| WILD | B3 | U | — † | — | fab | — | https://venturebeat.com/orchestration/ai-agents-are-quietly-generating-chaos-engineering-failures-enterprises-dont-track-yet |
| WILD | B3 | U | — † | — | cur | — | https://www.weareyuma.com/en/insights/research/harnessing-chaos-implementing-chaos-engineering-azure-chaos-studio-and-gremlin |

### 10.3.7

**Q:** Canonical failure taxonomy for agent runs (model error, tool error, infra failure, policy block, budget exhaustion, timeout, validation failure): one platform-owned schema feeding alerting (10.7.4), error budgets (10.3.4), and analysis (7.1.1)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://github.com/microsoft/AgentRx |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/drewmattie-code/Agent-Failure-Attribution |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/supernovae-st/nika-spec/blob/main/spec/05-errors.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/tangle-network/agent-eval/blob/48fcaf8e/src/trace/schema.ts |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.03105 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.20785 |
| research | B2 | T3 | 2026-04 | url | fab | — | https://arxiv.org/pdf/2604.23581 |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.20576 |
| research | B2 | T3 | 2026-02-01 | exc | kim | — | https://arxiv.org/pdf/2602.02475 |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.14647 |
| research | B3 | T3 | — † | — | kim | — | https://bijux.io/bijux-canon/05-bijux-canon-agent/architecture/error-model/ |
| research | B3 | T3 | — † | — | kim | — | https://web.cs.dal.ca/~mehil/TOSEM26_Faults_in_Agents.pdf |
| WILD | B1 | U | 2026-07 | exc | fab | — | https://www.openlayer.com/blog/ai-agent-failure-modes-tool-calling-loops-propagation |
| WILD | B2 | U | 2026 | exc | fab | — | https://futureagi.com/glossary/failure-modes-in-ai/ |
| WILD | B2 | U | 2026 | exc | fab | — | https://www.metacto.com/blogs/ai-agent-failures-and-how-to-avoid-them |
| WILD | B2 | U | 2026 | exc | fab | — | https://uptrace.dev/blog/opentelemetry-ai-systems |
| WILD | B3 | U | — † | — | fab | — | https://latitude.so/blog/ai-agent-failure-detection-guide |

### 10.4.1

**Q:** Unit of attribution: request, agent, workflow, tenant, user; tags carried from intake (2.1) onward.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://agnt.gg/docs/api/ledger-wallets |
| primary | B3 | T2 | — † | — | cur | — | https://braceframework.org/guides/agent/ |
| research | B3 | T3 | — † | — | kim | — | https://agentping.io/blog/multi-agent-cost-attribution |
| research | B3 | T3 | — † | — | fab | — | https://www.braintrust.dev/articles/how-to-track-llm-costs-2026 |
| research | B3 | T3 | — † | — | fab kim | — | https://www.digitalapplied.com/blog/llm-agent-cost-attribution-guide-production-2026 |
| research | B3 | T3 | — † | — | cur kim | — | https://dreaming.press/posts/llm-cost-attribution-per-agent-and-tenant.html |
| research | B3 | T3 | — † | — | fab | — | https://www.finout.io/blog/ai-cost-visibility-in-2026-strategies-tools-and-best-practices |
| research | B3 | T3 | — † | — | fab | — | https://www.finout.io/blog/finops-for-ai-agents-a-four-step-allocation-framework |
| research | B3 | T3 | — † | — | cur | — | https://mortalapps.com/agents/production-engineering/tracing-multi-agent-workflows/ |
| research | B3 | T3 | — † | — | cur kim | 10.4.5 | https://praesidia.ai/blog/spend-attribution-per-agent-showback |
| WILD | B2 | U | 2026 | url | cur | — | https://dev.to/sol_causely/ai-api-cost-attribution-in-2026-how-to-track-llm-spend-by-team-and-request-3h7g |
| WILD | B3 | U | — † | — | fab | — | https://amnic.com/blogs/top-ai-agent-tools-for-finops |
| WILD | B3 | U | — † | — | fab | — | https://www.boundev.ai/blog/llm-cost-attribution-per-feature |
| WILD | B3 | U | — † | — | fab | — | https://www.mavvrik.ai/blog/how-to-track-ai-costs/ |
| WILD | B3 | U | — † | — | fab | — | https://www.metacto.com/blogs/llm-cost-attribution-per-user-feature |
| WILD | B3 | U | — † | — | fab | — | https://www.mintmcp.com/blog/llm-cost-optimization-agent-teams |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/articles/llm-cost-attribution-needs-request-level-metadata-not-invoices/ |
| WILD | B3 | U | — † | — | fab | — | https://omnithium.ai/blog/ai-agent-cost-attribution.html |
| WILD | B3 | U | — † | — | fab | — | https://opsmeter.io/blog/llm-cost-attribution |
| WILD | B3 | U | — † | — | fab | — | https://praesidia.ai/guides/ai-finops |
| WILD | B3 | U | — † | — | fab | — | https://www.spheron.network/blog/gpu-cloud-finops-ai-teams-cost-allocation-chargeback-budgeting/ |
| WILD | B3 | U | — † | — | fab | — | https://www.youtube.com/watch?v=2okjGf8zVwE |

### 10.4.2

**Q:** Metering source of truth: tokens at the gateway (3.2), compute at the scheduler (4.2); tags on every allocation.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-05 | url | fab | — | https://www.cncf.io/blog/2026/08/05/opencost-1-121-0-first-of-a-kind-kubernetes-inference-cost-tracking/ |
| primary | B3 | T2 | — † | — | kim | — | https://docs.litellm.ai/docs/troubleshoot/cost_discrepancy |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/aws-samples/sample-agentcore-gateway-usage-interceptor |
| primary | B3 | T2 | — † | — | fab kim | 10.4.5 | https://konghq.com/blog/enterprise/llm-cost-management-ai-showback-and-chargeback |
| research | B2 | T3 | 2026-05-13 | url | kim | — | https://tianpan.co/blog/2026-05-13-token-accounting-drift-trace-logs-vs-provider-invoice |
| research | B3 | T3 | — † | — | kim | — | https://agustin-otegui.com/knowledge/how_does_ai_gateway_token_metering_architecture_actually_work_and_how_should_i_design_one_in_2026.php |
| research | B3 | T3 | — † | — | cur | — | https://champlinenterprises.com/blog/usage-based-metering-architecture-designing-ingestion-engine |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/aiwave/build-a-streaming-usage-ledger-for-openai-compatible-ai-gateways-1ea5 |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/kral-ai/billing-llm-usage-per-token-the-pitfalls-nobody-warns-you-about-oge |
| research | B3 | T3 | — † | — | fab | — | https://www.getmaxim.ai/articles/tracking-llm-token-usage-across-providers-teams-and-workloads/ |
| research | B3 | T3 | — † | — | cur | — | https://www.kunwar.page/chapter/083-metering-and-billing-pipelines |
| research | B3 | T3 | — † | — | fab | — | https://mlflow.org/articles/token-usage-tracking/ |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/token-count-mismatch |
| research | B3 | T3 | — † | — | fab | — | https://portkey.ai/blog/tracking-llm-token-usage-across-providers-teams-and-workloads/ |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/blog/best-llm-cost-tracking-tools-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.getmaxim.ai/articles/best-llm-cost-tracking-tools-in-2026/ |
| WILD | B3 | U | — † | — | cur | — | https://nhimg.org/articles/ai-chargeback-needs-gateway-level-metering-not-spreadsheet-estimates/ |
| WILD | B3 | U | — † | — | cur | — | https://nhimg.org/faq/why-do-ai-chargeback-programmes-fail-without-gateway-metering/ |
| WILD | B3 | U | — † | — | fab | — | https://superpenguin.ai/blog/best-llm-cost-tracking-tools |
| WILD | B3 | U | — † | — | fab | — | https://sysart.consulting/insights/token-budget-management-on-premises-llm/ |
| WILD | B3 | U | — † | — | fab | — | https://www.toriihq.com/articles/seven-tools-for-tracking-ai-token-usage-across-vendors |
| WILD | B3 | U | — † | — | fab | 10.4.4 | https://usagebox.com/articles/llm-gateway-cost-control-token-quotas-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.worklytics.co/blog/how-to-track-llm-token-usage-and-cost |

### 10.4.3

**Q:** Cost data format — FinOps FOCUS spec, or internal?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-06-04 | exc | fab kim | — | https://focus.finops.org/focus-specification/ |
| core | B3 | T1 | — † | — | gpt | — | https://www.finops.org/topic/focus/ |
| core | B3 | T1 | — † | — | gpt | — | https://www.finops.org/wg/adopting-focus-the-finops-open-cost-and-usage-specification/ |
| core | B3 | T1 | — † | — | cur fab gpt | — | https://focus.finops.org/what-is-focus/ |
| core | B3 | T1 | — † | — | fab kim | — | https://focus.finops.org/focus-specification/v1-2/ |
| core | B3 | T1 | — † | — | fab | — | https://focus.finops.org/focus-specification/v1-1/ |
| core | B3 | T1 | — † | — | fab | — | https://focus.finops.org/focus-specification/v1-0/ |
| core | B3 | T1 | — † | — | kim | — | https://focus.finops.org/focus-1-5-release-scope/ |
| core | B3 | T1 | — † | — | kim | — | https://focus.finops.org/docs/specification/v1-4/columns/cost-and-usage/sku-price-details/ |
| core | B3 | T1 | — † | — | gpt | — | https://focus.finops.org/ |
| core | B3 | T1 | — † | — | gpt | — | https://focus.finops.org/docs/specification/v1-3/columns/billed-cost/ |
| core | B3 | T1 | — † | — | gpt | — | https://focus.finops.org/docs/specification/v1-0/columns/cost-and-usage/billed-cost/ |
| core | B3 | T1 | — † | — | gpt | — | https://focus.finops.org/docs/specification/v1-4/ |
| core | B3 | T1 | — † | — | gpt | — | https://focus.finops.org/docs/specification/v1-3/ |
| core | B3 | T1 | — † | — | cur | — | https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec/ |
| core | B3 | T1 | — † | — | kim | — | https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec/issues/2018 |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec |
| core | B3 | T1 | — † | — | gpt | — | https://github.com/FinOps-Open-Cost-and-Usage-Spec |
| core | B3 | T1 | — † | — | fab | — | https://www.linuxfoundation.org/press/finops-foundation-launches-focus-1.3-to-deepen-cloud-and-saas-billing-transparency-announces-expanded-vendor-support-for-focus-1.2 |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/glassity/focus-mcp |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/wisk-aero-oss/finops-agents |
| research | B3 | T3 | — † | — | cur | — | https://cloudcostroom.com/blog/how-to-ingest-focus-billing-exports-into-a-data-warehouse |
| research | B3 | T3 | — † | — | cur | — | https://cloudcostroom.com/blog/how-to-build-a-cost-allocation-model-with-focus-data |
| research | B3 | T3 | — † | — | cur | — | https://cloudcostroom.com/blog/how-to-build-cost-data-pipelines-with-focus |
| research | B3 | T3 | — † | — | fab | — | https://www.flexera.com/blog/perspectives/finops-x-2026-recap/ |
| WILD | B2 | U | 2026-06 | url | fab | — | https://software.strategy.com/blog/june-2026-smarter-cost-control-governed-ai-access-richer-mosaic-modeling |
| WILD | B3 | U | — † | — | fab | — | https://aicostcheck.com/blog/ai-model-pricing-trends-2026 |
| WILD | B3 | U | — † | — | fab | — | https://amnic.com/blogs/finops-open-cost-and-usage-specification-guide-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.devstars.com/blog/2026-ai-model-costs/ |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/ai-model-api-pricing-tracker-q2-2026-data-points |
| WILD | B3 | U | — † | — | fab | — | https://keyholesoftware.com/ai-software-development-cost-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://korixinc.com/learning-center/ai-pricing-models-2026 |
| WILD | B3 | U | — † | — | fab | — | https://newsletter.finopsweekly.com/p/finops-focus-for-2026 |
| WILD | B3 | U | — † | — | fab | — | https://oplexa.com/ai-inference-cost-crisis-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://sesamedisk.com/ai-inference-costs-2026/ |

### 10.4.4

**Q:** Budget enforcement: pre-flight in policy (2.2), hard stop at the gateway (3.2), or both?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://agentgateway.dev/docs/standalone/latest/llm/cost-controls/budget-limits/ |
| primary | B3 | T2 | — † | — | kim | — | https://agentgateway.dev/docs/standalone/main/llm/cost-controls/budget-limits/rate-limit/ |
| primary | B3 | T2 | — † | — | cur fab | — | https://aisecuritygateway.ai/docs/llm-budget-enforcement |
| primary | B3 | T2 | — † | — | cur kim | — | https://developers.cloudflare.com/ai-gateway/features/spend-limits/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.api7.ai/ai-gateway/traffic-controls/budgets |
| primary | B3 | T2 | — † | — | kim | — | https://docs.solo.io/agentgateway/latest/llm/cost-controls/budget-limits/ |
| primary | B3 | T2 | — † | — | cur | — | https://evalguard.ai/docs/budget |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/sakura-sky/tollgate |
| primary | B3 | T2 | — † | — | fab | — | https://mlflow.org/blog/gateway-budget-alerts-limits/ |
| research | B3 | T3 | — † | — | fab | — | https://www.bigeye.com/blog/how-to-track-ai-agent-costs-and-token-usage |
| research | B3 | T3 | — † | — | kim | — | https://www.calcis.dev/what-is-preflight-llm-cost-estimation |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/aiwave/build-a-tool-cost-preflight-for-ai-agent-gateways-2md6 |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/jackm-singularity/ai-agent-cost-forecasting-predict-workflow-spend-before-users-hit-run-190h |
| research | B3 | T3 | — † | — | fab | — | https://neuraltrust.ai/blog/ai-agent-security-enterprises-complete-guide |
| research | B3 | T3 | — † | — | fab | — | https://www.sakurasky.com/blog/tollgate-launch/ |
| WILD | B3 | U | — † | — | fab | — | https://agatsoftware.com/ai-agent-security-enterprise-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/blog/best-ai-gateways-token-budgeting-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.getmaxim.ai/articles/top-5-enterprise-ai-gateways-to-control-llm-spend-across-providers/ |
| WILD | B3 | U | — † | — | fab | — | https://www.kosmoy.com/resources/blog/best-ai-agent-governance-platforms-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.mintmcp.com/blog/ai-compliance-software-agent-deployments |

### 10.4.5

**Q:** Showback report contract; unit economics (cost per completed job, 5.3).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://blog.mean.ceo/llm-model-routing/ |
| research | B3 | T3 | — † | — | cur | — | https://cloudcostroom.com/blog/showback-vs-chargeback-an-implementation-guide |
| research | B3 | T3 | — † | — | fab | — | https://www.cloudzero.com/blog/ai-agent-cost/ |
| research | B3 | T3 | — † | — | kim | — | https://www.ibm.com/think/insights/ai-agent-token-spend-management |
| research | B3 | T3 | — † | — | kim | — | https://www.optimnow.io/post/why-traditional-finops-breaks-with-ai-workloads |
| research | B3 | T3 | — † | — | kim | — | https://www.usu.com/en/blog/cost-allocation-strategies-and-tokenomics |
| WILD | B1 | U | 2026-08-15 | url | fab | — | https://www.progressiverobot.com/2026/08/15/finops-for-ai-llm-agent-gpu-costs/ |
| WILD | B2 | U | 2026 | url | cur | — | https://www.mavvrik.ai/blog/chargeback-vs-showback/ |
| WILD | B3 | U | — † | — | fab | — | https://amnic.com/blogs/finops-tools-for-ai-cost-management |
| WILD | B3 | U | — † | — | fab | — | https://www.correlation-one.com/blog/how-to-manage-ai-token-costs-in-the-enterprise-the-2026-playbook |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/ai-agent-productivity-statistics-2026-roi-data-points |
| WILD | B3 | U | — † | — | cur | — | https://www.dolead.com/growth-hub/plumbing-marketing-pre-framing-leads-eliminate-sales-friction-3f6c0 |
| WILD | B3 | U | — † | — | fab | — | https://ecorpit.com/ai-agent-unit-economics-cost-per-task-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.finout.io/blog/best-finops-tools-for-managing-ai-costs-in-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.kunalganglani.com/blog/ai-agent-cost-per-task-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.opslyft.com/guides/ai-cost-optimization |
| WILD | B3 | U | — † | — | fab | — | https://pickaxe.co/post/ai-agent-pricing-models |
| WILD | B3 | U | — † | — | cur | — | https://pixlodo.com/finops-chargeback-showback/ |
| WILD | B3 | U | — † | — | fab | — | https://r-sun.ai/insights/ai-agents-vs-offshore-labor-economics-2026 |
| WILD | B3 | U | — † | — | fab | — | https://rickpollick.com/blog/finops-for-ai-llm-cost-governance |
| WILD | B3 | U | — † | — | fab | — | https://www.usage.ai/blogs/finops/ai-ml-cost/finops-x-2026-takeaways |
| WILD | B3 | U | — † | — | fab | — | https://wetheflywheel.com/en/guides/ai-finops-gpu-cost-management-2026/ |

### 10.5.1

**Q:** Classification scheme; attached at intake (2.1).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2023 | url | cur | — | https://nvlpubs.nist.gov/nistpubs/ir/2023/NIST.IR.8496.ipd.pdf |
| primary | B3 | T2 | — † | — | cur | — | https://www.conduktor.io/glossary/data-classification-and-tagging-strategies |
| primary | B3 | T2 | — † | — | cur kim | — | https://www.cyberhaven.com/infosec-essentials/what-is-data-classification |
| primary | B3 | T2 | — † | — | cur | — | https://developer.box.com/guides/metadata/classifications |
| primary | B3 | T2 | — † | — | cur | — | https://developers.tetrascience.com/v4.3/docs/basic-concepts-metadata-tags-and-labels |
| research | B2 | T3 | 2026-01 | url | fab | — | https://arxiv.org/pdf/2601.09717 |
| research | B3 | T3 | — † | — | kim | — | https://agentc2.ai/blog/ai-agent-sensitive-data-compliance |
| research | B3 | T3 | — † | — | fab | — | https://concentric.ai/a-2026-guide-to-automated-data-classification/ |
| research | B3 | T3 | — † | — | fab | — | https://concentric.ai/the-importance-of-data-classification-levels-and-labels/ |
| research | B3 | T3 | — † | — | fab | — | https://www.fortra.com/blog/what-are-data-classification-sensitivity-labels |
| research | B3 | T3 | — † | — | kim | — | https://playbook.agentskit.io/docs/pillars/security/data-classification-pattern |
| research | B3 | T3 | — † | — | kim | — | https://thedatagovernor.com/data-classification-implementation/ |
| research | B3 | T3 | — † | — | kim | — | https://thomasthelliez.com/blog/data-classification-enterprise-ai-assistants/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/ai-agent/data-for-ai/how-to-handle-pii-in-ai-pipelines/ |
| WILD | B3 | U | — † | — | fab | — | https://www.dpo-consulting.com/blog/gdpr-data-classification |
| WILD | B3 | U | — † | — | fab | — | https://iternal.ai/ai-data-classification |
| WILD | B3 | U | — † | — | fab | — | https://www.kiteworks.com/secure-file-transfer/data-classification/ |
| WILD | B3 | U | — † | — | fab | — | https://www.lightbeam.ai/resources/blogs/sensitive-data-in-ai-pipelines-why-data-classification-accuracy-is-now-a-board-level-problem/ |
| WILD | B3 | U | — † | — | fab | — | https://www.oliveandgoose.com/how-to-classify-and-protect-sensitive-data-in-ai-models/ |
| WILD | B3 | U | — † | — | fab | — | https://www.sentinelone.com/cybersecurity-101/data-and-ai/what-is-data-classification/ |
| WILD | B3 | U | — † | — | fab | — | https://www.strac.io/blog/data-classification-and-tagging-labeling |
| WILD | B3 | U | — † | — | fab | — | https://www.teleskope.ai/post/ai-data-classification |
| WILD | B3 | U | — † | — | fab | — | https://www.trustcloud.ai/grc/powerful-data-classification-policy-adapt-to-emerging-threats/ |
| WILD | B3 | U | — † | — | fab | — | https://ziloservices.com/blogs/data-classification-software/ |

### 10.5.2

**Q:** PII detection / redaction points: intake (2.1), memory (4.4), outputs (5.1), telemetry (6.1), knowledge (8.3).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | fab | — | https://arize.com/docs/ax/observe/tracing/configure/redact-sensitive-data-from-traces |
| primary | B3 | T2 | — † | — | fab | — | https://docs.databricks.com/gcp/en/mlflow3/genai/tracing/redact-pii-otel-traces |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/mxab/otel-presidio |
| primary | B3 | T2 | — † | — | kim | — | https://grafana.com/docs/grafana-cloud/observe-and-act/agent-observability/privacy-and-security/pii-and-secrets-redaction/ |
| primary | B3 | T2 | — † | — | cur | — | https://strandsagents.com/docs/user-guide/safety-security/pii-redaction/ |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.29567 |
| research | B2 | T3 | 2026-04-12 | url | cur | — | https://tianpan.co/blog/2026/04/12/pii-in-llm-pipelines |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.05618 |
| research | B2 | T3 | 2026-02-06 | url | fab | — | https://oneuptime.com/blog/post/2026-02-06-redact-sensitive-prompts-genai-opentelemetry-traces/view |
| research | B3 | T3 | 2025-12 | url | fab | — | https://arxiv.org/pdf/2512.12914 |
| research | B3 | T3 | — † | — | cur | — | https://www.agentpatternscatalog.org/patterns/pii-redaction/ |
| research | B3 | T3 | — † | — | fab kim | — | https://dev.to/gabrielanhaia/redacting-pii-in-llm-traces-without-losing-debuggability-2jll |
| research | B3 | T3 | — † | — | fab | — | https://www.gravitee.io/blog/how-to-prevent-pii-leaks-in-ai-systems-automated-data-redaction-for-llm-prompt |
| research | B3 | T3 | — † | — | cur kim | — | https://www.metacto.com/blogs/pii-redaction-llm-pipeline-production |
| research | B3 | T3 | — † | — | fab | — | https://predictionguard.com/blog/pii-detection-redaction-llm-pipelines-regulated-industries |
| research | B3 | T3 | — † | — | kim | — | https://prefactor.tech/learn/real-time-pii-detection |
| research | B3 | T3 | — † | — | fab | — | https://www.researchgate.net/publication/399533114_Safe_Observability_A_Framework_for_Automated_PII_Redaction_from_LLM_Prompts_in_OpenTelemetry_Pipelines |
| research | B3 | T3 | — † | — | cur kim | — | https://www.truefoundry.com/blog/pii-redaction-llm-gateway-vs-application |
| WILD | B2 | U | 2026-04 | url | fab | — | https://www.huuphan.com/2026/04/pii-detection-redaction-pipeline.html |
| WILD | B3 | U | — † | — | fab | — | https://nirajranasinghe.medium.com/redacting-pii-before-it-hits-the-llm-0fe9507f05e0 |
| WILD | B3 | U | — † | — | fab | — | https://philterd.ai/blog/ |
| WILD | B3 | U | — † | — | fab | — | https://wavect.io/blog/pii-redaction-before-llm-prompts/ |

### 10.5.3

**Q:** Retention per class; right-to-erasure across memory (4.4), traces (6.1), artifacts (8.2), knowledge (8.3).

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://blogs.oracle.com/developers/from-rag-to-memory-systems-building-stateful-ai-architecture |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/StephenSook/erasure-proof |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/sambhal-labs/vismaran |
| research | B1 | T3 | 2026-07-05 | url | fab kim | — | https://tianpan.co/blog/2026/07/05/the-user-you-cannot-delete-right-to-be-forgotten-in-ai |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.18497 |
| research | B2 | T3 | 2026-06-04 | url | cur kim | — | https://zylos.ai/research/2026-06-04-controlled-forgetting-ai-agent-memory-retention/ |
| research | B3 | T3 | 2025-03 | url | fab | — | https://arxiv.org/pdf/2503.01630 |
| research | B3 | T3 | 2024-12 | url | fab | — | https://arxiv.org/pdf/2412.06356 |
| research | B3 | T3 | 2023-11 | url | fab | — | https://arxiv.org/pdf/2311.10385 |
| research | B3 | T3 | — † | — | kim | — | https://www.adaptiverecall.com/enterprise-memory/right-to-be-forgotten.php |
| research | B3 | T3 | — † | — | kim | — | https://isimplifyme.com/blog/agent-data-retention |
| research | B3 | T3 | — † | — | cur | — | https://octamem.com/blog/gdpr-right-to-erasure-ai-memory |
| research | B3 | T3 | — † | — | cur kim | — | https://openzync.tech/blog/right-to-be-forgotten-agent-memory |
| research | B3 | T3 | — † | — | kim | — | https://sota.io/blog/eu-ai-act-agentic-ai-memory-rag-compliance-gdpr-vector-stores-2026 |
| WILD | B2 | U | 2026-04-28 | url | fab | — | https://zylos.ai/research/2026-04-28-memory-privacy-retention-persistent-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/ai-agent-memory-governance/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/data-privacy-for-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://atlan.com/know/ai-agent/gdpr-compliance-for-ai-agents/ |
| WILD | B3 | U | — † | — | fab | — | https://www.codebridge.tech/articles/ai-memory-privacy-and-security |
| WILD | B3 | U | — † | — | fab | — | https://kronvex.io/blog-gdpr-ai-agents |
| WILD | B3 | U | — † | — | fab | — | https://mixpeek.com/guides/deleting-data-from-a-vector-index |
| WILD | B3 | U | — † | — | fab | — | https://sota.io/blog/eu-ai-act-gdpr-art17-right-erasure-training-data-llm-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.techpolicy.press/the-right-to-be-forgotten-is-dead-data-lives-forever-in-ai/ |
| WILD | B3 | U | — † | — | fab | — | https://www.twig.so/dev/rag-scenarios-and-solutions/privacy/gdpr-compliance |

### 10.5.4

**Q:** Residency constraints per class; allowed providers / regions.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://anyrouter.dev/docs/guides/provider-routing.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ashiqrniloy/prism/blob/main/docs/model-routing.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ashiqrniloy/prism/blob/main/packages/model-router/src/types.ts |
| primary | B3 | T2 | — † | — | cur | — | https://openrouter.ai/blog/insights/ai-data-residency/ |
| primary | B3 | T2 | — † | — | cur | — | https://openrouter.ai/blog/announcements/us-in-region-routing/ |
| primary | B3 | T2 | — † | — | kim | — | https://openrouter.ai/docs/guides/features/sovereign-ai |
| primary | B3 | T2 | — † | — | kim | — | https://vercel.com/docs/ai-gateway/security-and-compliance/regional-inference |
| research | B3 | T3 | — † | — | fab kim | — | https://lyceum.technology/magazine/eu-data-residency-ai-infrastructure/ |
| research | B3 | T3 | — † | — | fab | — | https://neuraltrust.ai/blog/data-sovereignty-complete-guide |
| research | B3 | T3 | — † | — | kim | — | https://www.truefoundry.com/blog/ai-gateway-data-residency-comparison |
| WILD | B3 | U | — † | — | fab | — | https://beyondscale.tech/blog/ai-data-residency-sovereignty-gdpr-cloud-act |
| WILD | B3 | U | — † | — | fab | — | https://connic.co/blog/ai-agent-platforms-eu-data-residency |
| WILD | B3 | U | — † | — | fab | — | https://decagon.ai/glossary/what-is-data-residency |
| WILD | B3 | U | — † | — | fab | — | https://dobby-ai.com/academy/data-residency-gdpr |
| WILD | B3 | U | — † | — | fab | — | https://www.edenai.co/post/best-european-ai-inference-providers |
| WILD | B3 | U | — † | — | fab | — | https://www.gmicloud.ai/ja/blog/data-residency-for-ai-workloads-what-enterprises-need-to-know-before-choosing-a-cloud-provider |
| WILD | B3 | U | — † | — | fab | — | https://www.hymalaia.com/blog/data-residency-compliance-for-ai-deployment-2026-guide-en |
| WILD | B3 | U | — † | — | fab | — | https://irisagent.com/blog/ai-customer-support-data-residency/ |
| WILD | B3 | U | — † | — | fab | — | https://www.premai.io/blog/ai-data-residency-requirements-by-region-the-complete-enterprise-compliance-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://renlayer.com/blog/data-residency-ai-agents-compliance |
| WILD | B3 | U | — † | — | fab | — | https://techplustrends.com/eu-sovereign-ai-infrastructure-stack-2026-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://vstorm.co/agentic-ai/ai-platforms/sovereign-ai-platforms-europe/ |
| WILD | B3 | U | — † | — | fab | — | https://wavect.io/blog/eu-data-residency-ai-apps-2026/ |

### 10.5.5

**Q:** DLP tooling pluggable, or policy-engine (2.2) rules?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://developers.cloudflare.com/ai-gateway/features/dlp/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.netskope.com/en/custom-file-classification-plugin |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/fabriziosalmi/aidlp |
| primary | B3 | T2 | — † | — | cur | — | https://help.zscaler.com/zia/adding-custom-dlp-engine |
| primary | B3 | T2 | — † | — | cur | — | https://learn.microsoft.com/en-us/windows/apps/develop/windows-integration/recall/dlp-provider-api |
| primary | B3 | T2 | — † | — | cur | — | https://techdocs.broadcom.com/us/en/symantec-security-software/information-security/data-loss-prevention/25-1/about-data-loss-prevention-policy-authoring/configuring-policy-rules.html |
| primary | B3 | T2 | — † | — | cur | — | https://techdocs.broadcom.com/content/dam/broadcom/techdocs/symantec-security-software/information-security/data-loss-prevention/generated-pdfs/Symantec_DLP_15.8_CE_Plugin_Developers_Guide.pdf |
| primary | B3 | T2 | — † | — | fab | — | https://www.truefoundry.com/docs/ai-gateway/opa-guardrails |
| research | B2 | T3 | 2026-04-26 | url | kim | — | https://tianpan.co/blog/2026/04/26/dlp-ai-gateway-egress-checkpoint |
| research | B2 | T3 | 2026-04-02 | url | fab | — | https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/ |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.07006 |
| research | B3 | T3 | — † | — | fab | — | https://codilime.com/blog/why-use-open-policy-agent-for-your-ai-agents/ |
| research | B3 | T3 | — † | — | kim | — | https://data443.com/blog/ai-gateway-vs-dlp-vs-waf-securing-llm-traffic-explained/ |
| research | B3 | T3 | — † | — | kim | — | https://devcheolu.com/en/posts/Mj3wwrnf3tesxwVWt15J |
| research | B3 | T3 | — † | — | kim | — | https://jozu.com/blog/ai-agent-governance-vs-iam-vs-dlp-vs-api-gateways/ |
| research | B3 | T3 | — † | — | kim | — | https://www.permit.io/blog/opa-for-protecting-ai-agents-and-agentic-stacks |
| research | B3 | T3 | — † | — | fab | — | https://www.security.com/feature-stories/symantec-dlp-google-agent-gateway-agentic-ai-security |
| WILD | B3 | U | 2025-11-21 | exc | fab | — | https://zenodo.org/records/19022572 |
| WILD | B3 | U | — † | — | fab | — | https://www.advantage.tech/data-loss-prevention-rules-for-llm-workflows/ |
| WILD | B3 | U | — † | — | fab | — | https://appscale.blog/en/blog/shadow-ai-dlp-preventing-pii-secret-leakage-public-llms-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.mintmcp.com/blog/dlp-solutions-ai-agents-llm-tool-calls |
| WILD | B3 | U | — † | — | fab | — | https://www.nightfall.ai/blog/network-dlp-solutions |
| WILD | B3 | U | — † | — | fab | — | https://www.strac.io/blog/ai-dlp |
| WILD | B3 | U | — † | — | fab | — | https://substack.com/home/post/p-195769034 |
| WILD | B3 | U | — † | — | fab | — | https://syntalith.ai/en/blog/opa-policy-layer-for-ai-agents-2026 |

### 10.6.1

**Q:** Provider port decided in 3.2 — what capability is lost by normalizing?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://ai.google.dev/gemini-api/docs/openai |
| primary | B3 | T2 | — † | — | cur | — | https://docs.api7.ai/ai-gateway/providers/compatibility |
| primary | B3 | T2 | — † | — | fab | — | https://docs.litellm.ai/docs/providers/openai_compatible |
| primary | B3 | T2 | — † | — | fab | — | https://docs.litellm.ai/docs/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Azure-Samples/ai-hub-gateway-solution-accelerator/blob/citadel-v1/guides/llm-access-guide.md |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/BerriAI/litellm |
| primary | B3 | T2 | — † | — | fab | — | https://www.litellm.ai/ |
| primary | B3 | T2 | — † | — | kim | — | https://ogx-ai.github.io/docs/api-openai/provider_matrix |
| research | B2 | T3 | 2026-04-20 | url | kim | — | https://tianpan.co/blog/2026-04-20-model-portability-tax-ai-systems-migration |
| research | B3 | T3 | 2025-09 | url | fab | — | https://arxiv.org/pdf/2509.02449 |
| research | B3 | T3 | — † | — | cur | — | https://bittide.aicompass.dev/article/4a431343-49e1-4f4c-ab49-d9cf692ec123 |
| research | B3 | T3 | — † | — | fab | — | https://openrouter.ai/blog/insights/llm-gateway/ |
| research | B3 | T3 | — † | — | kim | — | https://otf-kit.dev/blog/ai-provider-portability |
| research | B3 | T3 | — † | — | cur | — | https://www.requesty.ai/blog/do-provider-native-tools-work-through-an-llm-gateway |
| research | B3 | T3 | — † | — | kim | — | https://therouter.ai/blog/llm-function-calling-tool-use-cross-provider-comparison/ |
| research | B3 | T3 | — † | — | fab | — | https://www.truefoundry.com/blog/llm-gateway |
| WILD | B3 | U | — † | — | fab | — | https://axiomstudio.ai/blog/top-7-llm-gateway-solutions-enterprise-comparison |
| WILD | B3 | U | — † | — | fab | — | https://www.dataquest.io/blog/build-a-multi-provider-llm-gateway/ |
| WILD | B3 | U | — † | — | cur | — | https://dev.to/chrisl_8197/why-we-built-an-ai-gateway-with-three-native-api-formats-not-just-openai-compatible-45ah |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/elsie-rainee/comparing-open-source-llm-gateways-in-2026-to-run-enterprise-ai-at-scale-4h4p |
| WILD | B3 | U | — † | — | fab | — | https://gate.ai/blog/what-is-an-llm-gateway-how-enterprises-manage-model-calls-through-a-unified-layer |
| WILD | B3 | U | — † | — | fab | — | https://github.com/zeroclaw-labs/zeroclaw/issues/2602 |
| WILD | B3 | U | — † | — | fab | — | https://localaimaster.com/blog/ai-gateway-litellm |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@yadav.navya1601/what-is-an-llm-gateway-understanding-the-infrastructure-layer-for-multi-model-ai-fea4fecbc931 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@mrutyunjaya.mohapatra/litellm-a-unified-llm-api-gateway-for-enterprise-ai-de23e29e9e68 |
| WILD | B3 | U | — † | — | fab | — | https://www.tencentcloud.com/techpedia/143947 |

### 10.6.2

**Q:** Model catalog format (model cards) in the registry (8.5); who can add a model?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://huggingface.co/docs/hub/main/en/model-cards |
| primary | B1 | T2 | 2026-06-30 | exc | cur | — | https://github.com/kevinqz/coreai-catalog/blob/main/CONTRIBUTING.md |
| primary | B3 | T2 | — † | — | cur | — | https://aws.amazon.com/blogs/machine-learning/govern-models-with-mlflow-and-amazon-sagemaker-ai-model-registry-sync-part-2/ |
| primary | B3 | T2 | — † | — | fab gpt | — | https://docs.aws.amazon.com/sagemaker/latest/dg/model-cards.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/sagemaker/latest/dg/model-cards-create.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html |
| primary | B3 | T2 | — † | — | fab | — | https://docs.aws.amazon.com/sagemaker-unified-studio/latest/userguide/sagemaker-register-models.xml.html |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.aws.amazon.com/sagemaker/latest/dg/model-cards-faqs.html |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.aws.amazon.com/en_en/sagemaker/latest/dg/model-cards.html |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.aws.amazon.com/he_il/sagemaker/latest/dg/model-cards-faqs.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.datahub.com/docs/features/feature-guides/agent-registry |
| primary | B3 | T2 | — † | — | cur | — | https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4/html-single/managing_model_registries/index |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kubeflow/model-registry/blob/main/catalog/README.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kubeflow/model-registry/blob/v0.3.7/api/openapi/model-registry.yaml |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/linkml/model-card-schema/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.gravitee.io/platform/ai-catalog |
| primary | B3 | T2 | — † | — | cur | — | https://opendatahub.io/docs/working-with-model-registries/ |
| research | B2 | T3 | 2026-02-17 | url | fab | — | https://oneuptime.com/blog/post/2026-02-17-how-to-implement-model-cards-for-ml-model-documentation-on-vertex-ai/view |
| WILD | B2 | U | 2026-04-16 | url | fab | — | https://www.acejournal.org/2026/04/16/model-cards-as-governance-artifacts-gaps-and-enforcement |
| WILD | B3 | U | — † | — | fab | — | https://aisecurityandsafety.org/en/guides/ai-model-registries/ |
| WILD | B3 | U | — † | — | gpt | — | https://www.bridgebench.ai/models/cards |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/model-cards |
| WILD | B3 | U | — † | — | fab | — | https://kanerika.com/blogs/mlflow-model-registry-vs-hugging-face-hub-vs-azure-ml/ |
| WILD | B3 | U | — † | — | fab | — | https://www.programming-helper.com/tech/ai-model-governance-2026-model-registry-mlflow-enterprise-compliance |
| WILD | B3 | U | — † | — | fab | — | https://www.techaheadcorp.com/blog/ai-model-cards-data-provenance/ |
| WILD | B3 | U | — † | — | fab | — | https://techjacksolutions.com/ai/model-card/ai-model-cards-for-beginners/ |

### 10.6.3

**Q:** Routing policy owner — gateway (3.2), planning (2.3), or policy (2.2)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2021 | url | cur | — | https://www.arin.net/vault/participate/policy/proposals/2021/ARIN_prop_298_orig/ |
| core | B3 | T1 | — † | — | cur | — | https://opennetworking.org/wp-content/uploads/2014/10/TR-521_SDN_Architecture_issue_1.1.pdf |
| core | B3 | T1 | — † | — | cur | — | https://www.rfc-editor.org/rfc/rfc9067.pdf |
| primary | B3 | T2 | — † | — | cur | — | https://docs.opensdn.io/opensdn-service-provider-focused-features-guide/opensdn-routing-policy-sp-features.html |
| primary | B3 | T2 | — † | — | cur | — | https://documentation.nokia.com/sar-gen-2/26-7/7705-sar/books/unicast-routing-protocols/route-policies.html |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/agent-axiom/agent-arch/blob/main/docs/book/part-vi/chapter-14.en.md |
| research | B1 | T3 | 2026-08-26 | exc | kim | — | https://nhimg.org/faq/who-is-accountable-when-ai-request-routing-access-control-or-usage-visibility-fa/ |
| research | B1 | T3 | 2026-06-20 | exc | kim | — | https://nhimg.org/faq/how-should-enterprises-govern-llm-routing-across-multiple-model-providers/ |
| research | B2 | T3 | 2026-03 | url | fab | — | https://arxiv.org/pdf/2603.21354 |
| research | B3 | T3 | — † | — | kim | — | https://agustin-otegui.com/knowledge/what_does_a_working_agentic_ai_routing_governance_framework_look_like_in_2026_and_how_do_enterprises_actually_build_one.php |
| research | B3 | T3 | — † | — | kim | — | https://platformengineering.com/features/the-platform-team-just-became-the-agent-team-and-nobody-sent-a-memo/ |
| research | B3 | T3 | — † | — | kim | — | https://www.socratopia.app/library/ai-engineering-en/chapter-17 |
| WILD | B3 | U | — † | — | fab | 10.6.4 | https://www.digitalapplied.com/blog/llm-model-routing-2026-cost-quality-optimization-engineering-guide |
| WILD | B3 | U | — † | — | fab | — | https://www.getmaxim.ai/articles/top-5-llm-gateways-in-2026-a-production-ready-comparison/ |
| WILD | B3 | U | — † | — | fab | — | https://www.getmaxim.ai/articles/top-5-llm-router-solutions-in-2026/ |
| WILD | B3 | U | — † | — | fab | 10.6.4 | https://inworld.ai/resources/best-llm-router-ai-gateway |
| WILD | B3 | U | — † | — | fab | — | https://www.kosmoy.com/resources/blog/why-every-company-running-more-than-one-llm-needs-an-ai-gateway/ |
| WILD | B3 | U | — † | — | fab | — | https://pinggy.io/blog/best_ai_llm_routers_openrouter_alternatives/ |

### 10.6.4

**Q:** Routing reads the registry (8.5) as its only source?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-04 | exc | kim | — | https://developers.googleblog.com/en/a-unified-api-for-ai-model-routing/ |
| primary | B2 | T2 | 2026-04-26 | exc | kim | — | https://github.com/styrene-lab/omegon/commit/a83cee46c867799f11e0e36325c7b8dde5bcdc75 |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/yamanahlawat/llm-registry |
| primary | B3 | T2 | — † | — | fab | — | https://github.com/ulab-uiuc/LLMRouter |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/constructorfabric/gears-rust/blob/main/gears/model-registry/docs/PRD.md |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/tinyhumansai/tinyagents/blob/51752da2/src/registry/router/mod.rs |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/minhaozhang/ModelGate |
| primary | B3 | T2 | — † | — | fab | — | https://llm-router.cloud/ |
| primary | B3 | T2 | — † | — | fab | 10.6.5 | https://llmgateway.io/changelog |
| research | B3 | T3 | — † | — | fab | — | https://developers.googleblog.com/a-unified-api-for-ai-model-routing/ |
| research | B3 | T3 | — † | — | kim | — | https://www.developersdigest.tech/blog/models-dev-model-routing-infrastructure |
| WILD | B3 | U | — † | — | fab | — | https://aiprosol.com/llm-gateways |
| WILD | B3 | U | — † | — | fab | — | https://www.dataiku.com/blog/best-llm-gateways |
| WILD | B3 | U | — † | — | fab | — | https://www.lyzr.ai/blog/llm-gateway-architecture-guide |

### 10.6.5

**Q:** Fallback semantics: same-capability substitutes declared where? Prompt/model coupling tracked how?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/openwop/openwop/blob/main/RFCS/0031-envelope-variants-and-model-capabilities.md |
| primary | B3 | T2 | — † | — | cur | — | https://mono-agent-docs.vercel.app/runtime/fallback/ |
| research | B1 | T3 | 2026-09 | url | fab | — | https://arxiv.org/html/2609.00468v1 |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.08028 |
| research | B2 | T3 | 2026-06-03 | url | kim | — | https://tianpan.co/blog/2026/06/03/the-fallback-model-whose-system-prompt-was-tuned-for-someone-else |
| research | B2 | T3 | 2026-04-17 | url | kim | — | https://tianpan.co/blog/2026-04-17-prompt-model-coupling-trap |
| research | B2 | T3 | 2026-04-13 | url | kim | — | https://tianpan.co/blog/2026/04/13/llm-provider-lock-in-myth-and-reality |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2604.27789v1 |
| research | B3 | T3 | — † | — | fab | — | https://ckeditor.com/blog/llm-model-fallback-product-strategy/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/multigrid/fallback-chains-what-to-do-when-a-model-is-down-f33 |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/prompt-portability |
| research | B3 | T3 | — † | — | fab | — | https://www.researchgate.net/publication/410548012_Enterprise_LLM_Router_Learning_Quality-Capacity-Capability_Trade-offs_from_2026_Model_Metadata |
| research | B3 | T3 | — † | — | cur fab | — | https://theroadtoenterprise.com/blog/model-agnostic-ai-layer-fallbacks |
| WILD | B3 | U | — † | — | fab | — | https://www.buildmvpfast.com/blog/llm-fallback-strategies-primary-model-secondary-model-2026 |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/blog/what-is-llm-fallback-strategy-2026/ |
| WILD | B3 | U | — † | — | cur | — | https://github.com/pydantic/pydantic-ai/issues/6575 |
| WILD | B3 | U | — † | — | cur | — | https://github.com/HarperFast/documentation/blob/main/reference/models/routing.md |
| WILD | B3 | U | — † | — | fab | — | https://lushbinary.com/blog/llm-gateway-model-routing-cost-optimization-guide/ |

### 10.6.6

**Q:** Promotion gate: which blind evaluations (7.3) must pass before a model is routable; does that include a responsible-AI suite (bias, safety, harmful-output rate) alongside task metrics, and who owns it?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/tangle-network/agent-eval/blob/main/docs/multi-shot-optimization.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/tangle-network/agent-eval/blob/48fcaf8e/tests/campaign/statistical-heldout.test.ts |
| primary | B3 | T2 | — † | — | kim | — | https://mlflow.org/articles/what-is-canary-deployment-ai/ |
| research | B3 | T3 | — † | — | kim | — | https://aitechconnect.in/tips/shadow-canary-deploys-llm-model-upgrades-2026 |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/timwang2001/MG-Agent/5.3-router-policy-comparison-and-promotion-gate |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/how-to-ship-ai-agent-changes-safely.html |
| research | B3 | T3 | — † | — | kim | — | https://www.featbit.co/blogs/what-is-an-offline-eval-gate |
| research | B3 | T3 | — † | — | fab | — | https://futureoflife.org/ai-safety-index-summer-2026/ |
| research | B3 | T3 | — † | — | fab | — | https://hai.stanford.edu/ai-index/2026-ai-index-report/responsible-ai |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/model-deploy-strategies |
| research | B3 | T3 | — † | — | kim | — | https://se-ml.github.io/best_practices/03-cont-int/ |
| WILD | B3 | U | — † | — | fab | — | https://aisecurityandsafety.org/en/guides/ai-model-evaluation/ |
| WILD | B3 | U | — † | — | fab | — | https://aisecurityandsafety.org/en/glossary/ai-safety-evaluation-framework/ |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/blog/best-ai-gateways-prompt-management-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/blog/llm-eval-bias-fairness-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.knowlee.ai/blog/llm-evaluation-enterprise-guide |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@multimodal_bench/iclr-2026-oral-papers-in-ai-safety-a-35-paper-deep-dive-b5f8a250a0d1 |
| WILD | B3 | U | — † | — | fab | — | https://pranavakailash.medium.com/how-to-evaluate-llm-performance-6-proven-methods-2026-bbfa85a3fb67 |
| WILD | B3 | U | — † | — | fab | — | https://www.testmuai.com/blog/llm-evaluation/ |

### 10.6.7

**Q:** Local / rented GPU (4.2) vs hosted API — selection rule per job class.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://www.tencentcloud.com/techpedia/144464 |
| research | B2 | T3 | 2026 | url | cur | — | https://www.digitalapplied.com/blog/gpu-buy-vs-rent-vs-cloud-ai-inference-2026-decision-guide |
| research | B2 | T3 | 2026 | exc | cur | — | https://perkstack.co/blog/self-host-vs-api |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/alpacked/the-self-hosted-llm-breakeven-point-isnt-2m-tokens-a-day-its-a-ratio-5geh |
| research | B3 | T3 | — † | — | kim | — | https://diffco.us/blog/self-hosted-vs-api-based-llms-the-2026-cost-and-control-tradeoff/ |
| research | B3 | T3 | — † | — | kim | — | https://eltherion.com/blog/production-model-selection-hosted-apis-vs-self-hosted-models |
| research | B3 | T3 | — † | — | kim | — | https://howaiworks.ai/blog/self-hosted-vs-api-llm-cost |
| research | B3 | T3 | — † | — | cur | — | https://hybrid-llm.com/strategy/guide/local-llm-vs-cloud-api-decision-framework/ |
| research | B3 | T3 | — † | — | cur | — | https://notacalculator.com/guides/local-vs-hosted-llms-guide |
| research | B3 | T3 | — † | — | kim | — | https://www.sitepoint.com/local-llms-vs-cloud-api-cost-analysis-2026/ |
| research | B3 | T3 | — † | — | kim | — | https://vensas.de/en/blog/local-ai-self-hosting-tco |
| WILD | B3 | U | — † | — | fab | — | https://www.aipricingmaster.com/blog/self-hosting-ai-models-cost-vs-api |
| WILD | B3 | U | — † | — | fab | — | https://ajprotech.com/self-hosted-llm-cost-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.braincuber.com/blog/self-hosted-llms-vs-api-based-llms-cost-performance-analysis |
| WILD | B3 | U | — † | — | fab | — | https://cloudzy.com/blog/self-hosting-open-weight-llm-gpu-vps-cost/ |
| WILD | B3 | U | — † | — | fab | — | https://devtk.ai/en/blog/self-hosting-llm-vs-api-cost-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/self-hosting-open-weight-llms-2026-deployment-decision-guide |
| WILD | B3 | U | — † | — | fab | — | https://gigagpu.com/is-self-hosting-llms-cheaper-than-apis/ |
| WILD | B3 | U | — † | — | fab | — | https://kkrfgroup.com/self-hosted-llm-vs-api-enterprise/ |
| WILD | B3 | U | — † | — | fab | — | https://www.kunalganglani.com/blog/local-llm-cost-breakeven |
| WILD | B3 | U | — † | — | fab | — | https://leanlm.ai/blog/self-hosting-llm-cost |
| WILD | B3 | U | — † | — | fab | — | https://www.parallelloop.io/blogs/ai-cost-api-vs-self-hosted |
| WILD | B3 | U | — † | — | fab | — | https://particula.tech/blog/self-host-llm-vs-api-break-even-math-2026 |
| WILD | B3 | U | — † | — | fab | — | https://www.sitepoint.com/self-hosted-llm-costs-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.spheron.network/blog/gpt-6-vs-self-hosted-llm-2026/ |

### 10.6.8

**Q:** Provider-side model drift: are routed models pinned to immutable version identifiers where available, and what detects a silently updated alias and re-triggers blind evaluation (7.3) and registry re-certification (8.5)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B1 | T3 | 2026-08-01 | exc | kim | — | https://arxiv.org/html/2608.11803 |
| research | B1 | T3 | 2026-07 | url | fab | — | https://arxiv.org/pdf/2607.04072 |
| research | B2 | T3 | 2026-06 | url | fab | — | https://arxiv.org/pdf/2606.29719 |
| research | B2 | T3 | 2026-05 | url | fab | — | https://arxiv.org/pdf/2605.22976 |
| research | B3 | T3 | 2025-12 | url | fab | — | https://arxiv.org/pdf/2512.18020 |
| research | B3 | T3 | — † | — | fab | — | https://agenta.ai/blog/prompt-drift |
| research | B3 | T3 | — † | — | kim | — | https://arxiv.org/html/2605.25673v1 |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/how-to-catch-a-silent-model-upgrade-hosted-endpoint-drift.html |
| research | B3 | T3 | — † | — | kim | — | https://multigrid.ai/learn/silent-model-updates |
| research | B3 | T3 | — † | — | kim | — | https://zustis.com/blog/model-id-not-a-lockfile.html |
| WILD | B1 | U | 2026-08-19 | exc | fab | — | https://www.digitalapplied.com/blog/glm-latest-floating-alias-model-pinning-risk |
| WILD | B2 | U | 2025-12-30 | url | fab | — | https://byaiteam.com/blog/2025/12/30/llm-model-drift-detect-prevent-and-mitigate-failures/ |
| WILD | B3 | U | — † | — | fab | — | https://ceaksan.com/en/llm-agentic-failure-modes |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/aiwithmohit/your-llm-is-lying-to-you-silently-4-statistical-signals-that-catch-drift-before-users-do-4cg2 |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.com/blog/model-vs-data-drift-how-to-identify-and-handle-it/ |
| WILD | B3 | U | — † | — | fab | — | https://galileo.ai/blog/best-llm-output-drift-monitoring-platforms |
| WILD | B3 | U | — † | — | fab | — | https://linesncircles.com/Blog/Enterprise/LLM_drift_detection |
| WILD | B3 | U | — † | — | fab | — | https://lyceum.technology/magazine/model-deprecation-risk-version-pinning-notice-periods/ |
| WILD | B3 | U | — † | — | fab | — | https://stackpulsar.com/blog/llm-model-drift-detection/ |

### 10.7.1

**Q:** Deployment unit and delivery: GitOps (Argo / Flux) or other; environment promotion path aligned with 7.4.

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur fab | — | https://akuity.io/blog/how-kargo-fixes-gitops-with-promotion |
| primary | B3 | T2 | — † | — | gpt | — | https://argo-gitops-promoter.readthedocs.io/en/latest/getting-started/ |
| primary | B3 | T2 | — † | — | gpt | — | https://argo-gitops-promoter.readthedocs.io/en/latest/gating-promotions/ |
| primary | B3 | T2 | — † | — | gpt | — | https://argo-gitops-promoter.readthedocs.io/en/latest/integrating-with-argocd/tutorial/ |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.redhat.com/en/documentation/red_hat_openshift_gitops/1.20/html/argo_rollouts/getting-started-with-argo-rollouts |
| primary | B3 | T2 | — † | — | gpt | — | https://docs.redhat.com/en/documentation/red_hat_openshift_gitops/1.21/html/argo_rollouts/getting-started-with-argo-rollouts |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/kubeswarm/kubeswarm |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/samyn92/agenticops-core |
| primary | B3 | T2 | — † | — | gpt | — | https://github.com/argoproj/gitops-engine/blob/master/docs/faq.md |
| primary | B3 | T2 | — † | — | kim | — | https://kagent.dev/ |
| primary | B3 | T2 | — † | — | cur | — | https://octopus.com/devops/argo-cd/argo-cd-vs-flux/ |
| primary | B3 | T2 | — † | — | cur | — | https://www.plural.sh/blog/argo-cd-vs-flux/ |
| research | B1 | T3 | 2026-07-24 | exc | kim | — | https://explore.n1n.ai/blog/gitops-for-ai-agents-memory-version-control-2026-07-24 |
| research | B2 | T3 | 2026-04-02 | url | kim | — | https://maniak.io/articles/2026-04-02-gitops-for-agents-deployment-and-management/ |
| research | B2 | T3 | 2026-03-18 | url | gpt | — | https://devstarsj.github.io/2026/03/18/gitops-argocd-flux-kubernetes-guide-2026/ |
| research | B2 | T3 | 2026-02 | url | fab | — | https://www.infoq.com/news/2026/02/argocd-33/ |
| research | B2 | T3 | 2026-02-26 | url | fab | — | https://oneuptime.com/blog/post/2026-02-26-argocd-environment-promotion/view |
| research | B3 | T3 | — † | — | fab | — | https://akuity.io/blog/argo-cd-flux-comparison |
| research | B3 | T3 | — † | — | fab | — | https://akuity.io/blog/gitops-best-practices-whitepaper |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/aws-builders/production-grade-gitops-on-aws-verified-release-promotion-across-eks-environments-with-argo-cd-and-1204 |
| research | B3 | T3 | — † | — | cur | — | https://devops-daily.com/posts/gitops-argocd-repository-structure-multi-environment |
| research | B3 | T3 | — † | — | kim | — | https://fast.io/resources/ai-agent-gitops/ |
| research | B3 | T3 | — † | — | kim | — | https://leminnov.blog/posts/sympozium/ |
| research | B3 | T3 | — † | — | fab | — | https://www.portainer.io/blog/argocd-vs-flux |
| WILD | B2 | U | 2026-05-25 | url | fab | — | https://devstarsj.github.io/devops/kubernetes/gitops/2026/05/25/gitops-argocd-vs-flux-kubernetes-cd-comparison-2026/ |
| WILD | B2 | U | 2026-03-23 | exc | gpt | — | https://www.linkedin.com/posts/argoproj_argocon-gitops-kubernetes-activity-7440070705519616000-7IoL |
| WILD | B3 | U | — † | — | fab | — | https://calmops.com/devops/gitops-2026-complete-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/mechcloud_academy/the-gitops-standard-in-2026-a-comparative-research-analysis-of-argocd-and-fluxcd-46d8 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/devops-ai-decoded/top-10-gitops-tools-for-continuous-delivery-in-2026-6c04b0788734 |
| WILD | B3 | U | — † | — | fab | — | https://medium.com/@nsalexamy/automated-promotion-pipeline-with-argo-cd-argo-rollouts-and-github-actions-4f7ca9b4f1cc |
| WILD | B3 | U | — † | — | fab | — | https://talkingtech.io/gitops-tools-comparison-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://tasrieit.com/blog/argocd-vs-flux-gitops-comparison-2026 |

### 10.7.2

**Q:** Ops monitoring / alerting vs telemetry (6.1): same pipeline or separate?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B2 | T2 | 2026 | exc | cur | — | https://www.atatus.com/blog/observability-pipelines/ |
| primary | B3 | T2 | 2024 | url | fab | — | https://opentelemetry.io/blog/2024/llm-observability/ |
| primary | B3 | T2 | — † | — | cur | — | https://cribl.io/blog/the-observability-pipeline/ |
| primary | B3 | T2 | — † | — | kim | — | https://grafana.com/docs/tempo/latest/set-up-for-tracing/instrument-send/set-up-collector/tail-sampling/policies-strategies/ |
| primary | B3 | T2 | — † | — | kim | — | https://llm-d.ai/blog/end-to-end-and-fine-grained-tracing-in-llm-d |
| primary | B3 | T2 | — † | — | cur | — | https://www.splunk.com/en_us/blog/learn/observability-vs-monitoring-vs-telemetry.html |
| research | B2 | T3 | 2026-03-14 | url | kim | — | https://oneuptime.com/blog/post/2026-03-14-how-to-monitor-ai-agents-in-production/view |
| research | B2 | T3 | 2026-02-06 | url | fab | — | https://oneuptime.com/blog/post/2026-02-06-monitor-alert-opentelemetry-pipeline-health/view |
| research | B3 | T3 | — † | — | cur | — | https://www.databahn.ai/blog/enterprise-observability-vs-security-telemetry |
| research | B3 | T3 | — † | — | kim | — | https://iancloud.ai/blog/llm-observability-self-hosted-inference-2026 |
| research | B3 | T3 | — † | — | fab | — | https://mlflow.org/articles/setting-up-llm-observability-pipelines-in-2026/ |
| research | B3 | T3 | — † | — | fab | — | https://mlflow.org/articles/what-is-agent-observability-a-2026-developer-guide/ |
| research | B3 | T3 | — † | — | kim | — | https://www.mongodb.com/company/blog/technical/agent-observability-monitoring-decisions-not-requests |
| research | B3 | T3 | — † | — | fab | — | https://openobserve.ai/blog/opentelemetry-for-llms/ |
| research | B3 | T3 | — † | — | kim | — | https://www.parseable.com/blog/observability-datalake |
| research | B3 | T3 | — † | — | cur | — | https://socprime.com/blog/what-is-an-observability-pipeline/ |
| WILD | B3 | U | — † | — | fab | — | https://www.apica.io/blog/opentelemetry-best-practices-for-improving-your-monitoring-and-observability/ |
| WILD | B3 | U | — † | — | fab | — | https://www.confident-ai.com/knowledge-base/compare/top-7-llm-observability-tools |
| WILD | B3 | U | — † | — | fab | — | https://currentaffair.today/blog/technology-13/opentelemetry-genai-semantic-conventions-2026-end-to-end-implementation-guide-for-llm-agent-observability-419 |
| WILD | B3 | U | — † | — | fab | — | https://rootly.com/sre/top-ai-observability-trends-shaping-2026-ops-teams-c8456 |

### 10.7.3

**Q:** Upgrade strategy per component; which can be upgraded independently?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://developers.cloudflare.com/agents/model-context-protocol/guides/migrate-to-mcp-sdk-v2/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.gitlab.com/update/zero_downtime/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.gitlab.com/18.8/update/zero_downtime/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.gitlab.com/17.9/update/with_downtime/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.gitlab.com/update/with_downtime/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.gitlab.com/17.11/update/zero_downtime/ |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/modelcontextprotocol/typescript-sdk/blob/main/docs/protocol-versions.md |
| primary | B3 | T2 | — † | — | kim | — | https://learn.microsoft.com/en-us/agent-framework/migration-guide/ |
| primary | B3 | T2 | — † | — | kim | — | https://ts.sdk.modelcontextprotocol.io/v2/migration/support-2026-07-28 |
| research | B2 | T3 | 2026-02-20 | url | fab | — | https://oneuptime.com/blog/post/2026-02-20-kubernetes-upgrade-strategy/view |
| research | B2 | T3 | 2026-02-19 | url | fab | — | https://blogs.vmware.com/cloud-foundation/2026/02/19/case-study-navigating-vks-upgrades-balancing-infrastructure-constraints-and-application-reality/ |
| research | B2 | T3 | 2026-02-09 | url | fab | — | https://oneuptime.com/blog/post/2026-02-09-cluster-upgrades-version-skew/view |
| research | B2 | T3 | 2026-02-02 | url | fab | — | https://oneuptime.com/blog/post/2026-02-02-kubernetes-upgrade-strategies/view |
| research | B3 | T3 | — † | — | kim | — | https://aaif.io/blog/safely-rolling-out-the-july-28-mcp-update-with-agentgateway |
| research | B3 | T3 | — † | — | kim | — | https://callsphere.ai/blog/upgrading-agent-frameworks-breaking-changes-dependency-updates.md |
| research | B3 | T3 | — † | — | fab | — | https://www.plural.sh/blog/kubernetes-upgrade-strategy/ |
| research | B3 | T3 | — † | — | fab | — | https://www.plural.sh/blog/kubernetes-compatibility-matrix/ |
| WILD | B3 | U | — † | — | fab | — | https://alexandre-vazquez.com/kubernetes-gateway-api-versions-compatibility-guide/ |
| WILD | B3 | U | — † | — | fab | — | https://kubegrade.com/kubernetes-upgrade-strategies/ |
| WILD | B3 | U | — † | — | fab | — | https://www.matterai.so/guides/platform-engineering-roadmap-platform-maturity-model-capability-assessment-and-strategy |
| WILD | B3 | U | — † | — | fab | — | https://source.android.com/docs/core/architecture/vintf/comp-matrices |
| WILD | B3 | U | — † | — | fab | — | https://stribog.com/blog/kubernetes-version-upgrade-deprecated-api-skew-migration-playbook |
| WILD | B3 | U | — † | — | fab | — | https://tasrieit.com/blog/kubernetes-upgrade-strategy-zero-downtime-guide-2026 |
| WILD | B3 | U | — † | — | fab | — | https://technav.ieee.org/topic/upgradability/ |
| WILD | B3 | U | — † | — | fab | — | https://us.fitgap.com/stack-guides/reducing-upgrade-failures-with-a-standardized-device-compatibility-and-version-matrix-stack |

### 10.7.4

**Q:** Runbooks and incident process; who is paged per layer?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://sre.google/workbook/incident-response/ |
| primary | B3 | T2 | — † | — | cur | — | https://www.atlassian.com/incident-management/on-call/escalation-policies |
| primary | B3 | T2 | — † | — | cur | — | https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/incident-management/on-call/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.pagerduty.com/eng/pagerduty-for-ai-how-the-sre-agent-triages-ai-incidents/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.pagerduty.com/resources/incident-management-response/learn/runbook-automation-incident-response/ |
| primary | B3 | T2 | — † | — | kim | — | https://www.pagerduty.com/eng/inside-pagerdutys-sre-agent-how-we-built-deep-incident-investigation/ |
| primary | B3 | T2 | — † | — | kim | — | https://sre.azure.com/docs/capabilities/incident-response-plans |
| research | B1 | T3 | 2026-09-09 | url | cur | — | https://www.pagerly.io/blog/on-call-escalation-policy-design-2026-09-09 |
| research | B3 | T3 | — † | — | cur | — | https://www.itoc360.com/escalation-policy/ |
| research | B3 | T3 | — † | — | kim | — | https://playbook.agentskit.io/docs/pillars/quality/alerting-runbooks-pattern |
| WILD | B2 | U | 2026-04-19 | url | fab | — | https://tianpan.co/blog/2026-04-19-ai-incident-response-playbook-llm-production |
| WILD | B2 | U | 2026-04-17 | url | fab | — | https://tianpan.co/blog/2026/04/17/on-call-runbook-ai-systems |
| WILD | B2 | U | 2026-04-12 | url | fab | — | https://tianpan.co/blog/2026-04-12-ai-assisted-incident-response-giving-your-on-call-agent-a-runbook |
| WILD | B3 | U | — † | — | fab | — | https://www.augmentcode.com/guides/ai-agents-incident-management |
| WILD | B3 | U | — † | — | fab | — | https://www.augmentcode.com/guides/ai-sre-incident-management |
| WILD | B3 | U | — † | — | fab | — | https://blog.pazi.ai/ai-agent-use-cases-for-operations-teams-2026/ |
| WILD | B3 | U | — † | — | fab | — | https://www.digitalapplied.com/blog/agentic-workflow-incident-response-playbook-2026 |
| WILD | B3 | U | — † | — | fab | — | https://futureagi.substack.com/p/the-llm-incident-runbook-six-steps-f27 |
| WILD | B3 | U | — † | — | fab | — | https://incident.io/blog/runbook-automation-tools-2026-the-complete-guide |
| WILD | B3 | U | — † | — | fab | — | https://metoro.io/blog/top-ai-incident-response-tools |
| WILD | B3 | U | — † | — | fab | — | https://rootly.com/ai-sre-guide |
| WILD | B3 | U | — † | — | fab | — | https://runframe.io/blog/your-ai-agent-just-handled-that-incident |
| WILD | B3 | U | — † | — | fab | — | https://squareops.com/blog/ai-powered-incident-response-reduce-mttr-sre/ |
| WILD | B3 | U | — † | — | fab | — | https://vibraniumlabs.ai/blog/top-ai-sre-agents |
| WILD | B3 | U | — † | — | fab | — | https://yisusvii.github.io/posts/ai-sre-news-2026/ |

### 10.7.5

**Q:** Configuration: one schema per box, versioned in source control (8.1)?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | fab | — | https://github.com/json-schema-org/json-schema-spec/blob/main/specs/jsonschema-core.md |
| core | B3 | T1 | — † | — | fab | — | https://www.ietf.org/archive/id/draft-abaris-json-dcm-00.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.pingidentity.com/pingds/8.1/config-guide/import-export.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.pingidentity.com/pingds/8.1/install-guide/file-layout.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.pingidentity.com/pingds/8.1/tools-reference/dsconfig.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.pingidentity.com/pingds/8.1/configref/objects-.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.pingidentity.com/pingds/8.1/config-guide/schema.html |
| primary | B3 | T2 | — † | — | kim | — | https://docs.solace.com/Agent-Mesh/Framework/building/declarative-config/index.htm |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/ensemble-edge/edgit |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/Apicurio/apicurio-registry-gitops-example |
| primary | B3 | T2 | — † | — | kim | — | https://github.com/user-1221/agentic-engineering-standard/blob/main/spec/04-registries.md |
| primary | B3 | T2 | — † | — | kim | — | https://pypi.org/project/akgentic-catalog/2.2.0/ |
| research | B3 | T3 | — † | — | kim | — | https://dev.to/beefedai/schema-first-configuration-treat-configuration-as-data-4757 |
| WILD | B2 | U | 2026-02 | exc | fab | — | https://medium.com/google-cloud/gitops-reimagined-a-declarative-configuration-as-data-approach-b83349e7762a |
| WILD | B3 | U | — † | — | fab | — | https://www.browserstack.com/guide/configuration-as-code |
| WILD | B3 | U | — † | — | fab | — | https://configu.com/blog/what-is-configuration-as-code-cac-and-5-tips-for-success/ |
| WILD | B3 | U | — † | — | fab | — | https://devsecopsschool.com/blog/config-as-code/ |
| WILD | B3 | U | — † | — | fab | — | https://github.com/topics/configuration-management |
| WILD | B3 | U | — † | — | fab | — | https://go-tools.org/blog/json-schema-validation-complete-guide |
| WILD | B3 | U | — † | — | fab | — | https://www.iru.com/blog/config-as-code-for-device-management |
| WILD | B3 | U | — † | — | fab | — | https://jsonwebtools.com/json-schema-guide |
| WILD | B3 | U | — † | — | fab | — | https://mintlify.wiki/json-schema-org/json-schema-spec/specification/core/versioning |
| WILD | B3 | U | — † | — | fab | — | https://offlinetools.org/a/json-formatter/schema-versioning-for-json-configuration-files |
| WILD | B3 | U | — † | — | fab | — | https://www.xopsschool.com/tutorials/configuration-as-code/ |

### 10.7.6

**Q:** Global kill switch and per-tenant pause, beyond per-workflow cancellation (2.4.6): who can invoke each, and what state do in-flight jobs land in — drained, checkpointed and suspended, or hard-killed?

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | kim | — | https://docs.gloo.com/forge/run/kill-switches |
| research | B2 | T3 | 2026-03-07 | url | fab | — | https://law.stanford.edu/2026/03/07/kill-switches-dont-work-if-the-agent-writes-the-policy-the-berkeley-agentic-ai-profile-through-the-ailccp-lens/ |
| research | B3 | T3 | — † | — | fab | — | https://accuknox.com/blog/ai-kill-switch-agentic-ai |
| research | B3 | T3 | — † | — | kim | — | https://www.agentpatterns.tech/en/governance/kill-switch |
| research | B3 | T3 | — † | — | kim | — | https://www.agentpatternscatalog.org/patterns/interruptible-agent-execution/ |
| research | B3 | T3 | — † | — | kim | — | https://aigovernance.com/controls/agent-kill-switch |
| research | B3 | T3 | — † | — | kim | — | https://dreaming.press/posts/how-to-build-a-runtime-kill-switch-for-your-ai-agent.html |
| research | B3 | T3 | — † | — | kim | — | https://geodocs.dev/ai-agents/agent-startup-shutdown-spec |
| research | B3 | T3 | — † | — | kim | — | https://kla.digital/blog/ai-agent-kill-switch-interception-architecture |
| research | B3 | T3 | — † | — | fab | — | https://www.straiker.ai/blog/agentic-kill-switch-for-ai-agents |
| research | B3 | T3 | — † | — | fab | — | https://www.straiker.ai/blog/agentic-kill-switch-for-coding-agents |
| WILD | B1 | U | 2026-07-27 | url | fab | — | https://www.manilatimes.net/2026/07/27/tmt-newswire/globenewswire/jetstream-releases-surgical-ai-kill-switch-to-shut-down-individual-agents/2392220 |
| WILD | B3 | U | — † | — | fab | — | https://authoritygate.com/newsletter/kill-switch-gap-agentic-ai/ |
| WILD | B3 | U | — † | — | fab | — | https://www.darkreading.com/cybersecurity-operations/defining-ai-kill-switch-hard-but-necessary |
| WILD | B3 | U | — † | — | fab | — | https://dev.to/brennhill/how-to-build-an-ai-kill-switch-and-why-every-agent-needs-one-2758 |
| WILD | B3 | U | — † | — | fab | — | https://killswitch.md/ |
| WILD | B3 | U | — † | — | fab | — | https://www.miniorange.com/blog/ai-kill-switch-architecture/ |
| WILD | B3 | U | — † | — | fab | — | https://nhimg.org/glossary/ai-kill-switch/ |
| WILD | B3 | U | — † | — | fab | — | https://www.pedowitzgroup.com/what-kill-switches-are-needed-for-ai-agents |
| WILD | B3 | U | — † | — | fab | — | https://www.pedowitzgroup.com/ai-agent-kill-switches-practical-safeguards-that-work |
| WILD | B3 | U | — † | — | fab | — | https://www.techtarget.com/ai/tip/Why-businesses-need-an-AI-agent-kill-switch |
| WILD | B3 | U | — † | — | fab | — | https://vaultak.com/blog/how-to-add-kill-switch-ai-agent |
| WILD | B3 | U | — † | — | fab | — | https://www.waxell.ai/blog/kill-switch-ai-agent-problem |

---

## Unaligned v1 questions

Questions from the v1 Cursor run with no v2.0 counterpart, tagged `run:id`.

### cursor:0.1.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | url | cur | — | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/authorization/index.mdx |
| primary | B3 | T2 | — † | — | cur | — | https://www.descope.com/blog/post/mcp-vs-a2a-auth |
| research | B3 | T3 | — † | — | cur | — | https://qubittool.com/blog/mcp-a2a-a2ui-protocol-stack-guide |

### cursor:0.1.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://www.cerbos.dev/blog/authzen-standards-based-authorization-for-enterprises |
| primary | B3 | T2 | — † | — | cur | — | https://docs.sphereon.com/edk/guides/authorization/overview |
| primary | B3 | T2 | — † | — | cur | — | https://zuplo.com/learning-center/fine-grained-api-authorization-rbac-authzen-gateway |
| WILD | B3 | U | — † | — | cur | — | https://docs.big-acl.com/authorization-landscape/openid-authzen/ |

### cursor:0.1.8

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026 | url | cur | — | https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/LLM01_PromptInjection.md |
| primary | B3 | T2 | — † | — | cur | — | https://www.permit.io/blog/tool-call-safety-is-not-text-safety-action-time-authorization |
| primary | B3 | T2 | — † | — | cur | — | https://veto.so/ai-agent-security |
| WILD | B1 | U | 2026-06-22 | exc | cur | — | https://nhimg.org/faq/how-should-security-teams-stop-prompt-injection-from-turning-into-tool-misuse/ |
| WILD | B3 | U | 2025 | url | cur | — | https://redbotsecurity.com/prompt-injection-attacks-ai-security-2025/ |

### cursor:0.2.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://csrc.nist.gov/glossary/term/policy_enforcement_point |
| core | B3 | T1 | — † | — | cur | — | https://doi.org/10.6028/nist.sp.800-207 |
| primary | B3 | T2 | — † | — | cur | — | https://www.aserto.com/blog/the-authorization-3-body-problem |
| WILD | B3 | U | — † | — | cur | — | https://www.intersecinc.com/blogs/the-logical-components-of-zero-trust |

### cursor:0.3.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/handbook-academy/engineering-handbook/blob/main/content/hld/part-6-reliability-and-operations/02-resilience-patterns.md |
| primary | B3 | T2 | — † | — | cur | — | https://orkes.io/blog/idempotency-and-retry-safety-in-distributed-workflows |
| research | B1 | T3 | 2026-08-14 | url | cur | — | https://oneuptime.com/blog/post/2026-08-14-retry-ownership-sdk-mesh-application/view |
| research | B1 | T3 | 2026-07-29 | url | cur | — | https://oneuptime.com/blog/post/2026-07-29-timeout-outage-cross-layer-retry-budget/view |
| research | B3 | T3 | — † | — | cur | — | https://stevekinney.com/writing/ai-gateway-durable-workflows |

### cursor:0.8.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/szl-holdings/platform/blob/main/docs/observability/genai-observability-spec.md |
| primary | B3 | T2 | — † | — | cur | — | https://learn.microsoft.com/en-us/security/zero-trust/sfi/observability-ai-systems |
| research | B2 | T3 | 2026 | exc | cur | — | https://novaaiops.com/observability |
| research | B3 | T3 | — † | — | cur | — | https://agent-axiom.github.io/agent-arch/en/book/part-viii/chapter-26/ |
| research | B3 | T3 | — † | — | cur | — | https://heavythoughtcloud.com/knowledge/minimum-useful-trace-for-ai-systems |

### cursor:0.8.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://www.w3.org/TR/trace-context-1/ |
| primary | B2 | T2 | 2026-02-06 | url | cur | — | https://oneuptime.com/blog/post/2026-02-06-composite-propagators-multi-format-support/view |
| primary | B3 | T2 | — † | — | cur | — | https://tessl.io/registry/tessl/pypi-opentelemetry-api/1.36.0/files/docs/propagation.md |
| research | B3 | T3 | — † | — | cur | — | https://notes.kodekloud.com/docs/Prep-Course-OpenTelemetry-Certified-Associate-OTCA-Certification/Span-Anatomy-and-Context-Propagation/Context-Propagation/page |

### cursor:0.8.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ksimback/looper/blob/main/RUNNER-CONTRACT.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/JSONbored/loopover/issues/4782 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/JSONbored/loopover/issues/4783 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/lookmanrays/codencer/blob/main/docs/internal/FLAGSHIP_PLANNER_LOOP.md |
| primary | B3 | T2 | — † | — | cur | — | https://huangruiteng.github.io/loopx/docs/guides/custom-agent-runner-integration/ |

### cursor:0.8.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://cloudinfrainsights.com/best-practices-for-vendor-consolidation-across-monitoring-logging-and-apm/ |
| research | B3 | T3 | — † | — | cur | — | https://www.crises-control.com/blogs/incident-management-software-governance/ |
| research | B3 | T3 | — † | — | cur | — | https://www.itoc360.com/incident-management-vs-problem-management/ |
| research | B3 | T3 | — † | — | cur | — | https://nhimg.org/faq/what-breaks-when-security-teams-add-more-tools-without-reducing-overlap/ |
| research | B3 | T3 | — † | — | cur | — | https://www.processdesigner.com/solutions/incident-response-runbooks-evidence-trails |

### cursor:0.8.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/existential-birds/daydream/blob/f2ef3cda/tests/contract/test_backend_step_parity.py |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/existential-birds/daydream/blob/f2ef3cda/tests/test_backend_conformance.py |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/existential-birds/daydream/blob/f2ef3cda/tests/contract/test_backend_codex_trajectory.py |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/existential-birds/daydream/blob/f2ef3cda/tests/contract/_loaders.py |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/EmpireTwo/gaze/pull/202 |

### cursor:1.0.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B1 | T3 | 2026-07-01 | exc | cur | — | https://dovecore.com/blog/normalize-before-you-orchestrate-etl-for-agent-inputs |
| research | B3 | T3 | — † | — | cur | — | https://bijux.io/bijux-canon/05-bijux-canon-agent/interfaces/data-contracts/ |
| research | B3 | T3 | — † | — | cur | — | https://github.com/NousResearch/hermes-agent/pull/90236 |

### cursor:1.1.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://mintlify.wiki/agentclientprotocol/typescript-sdk/concepts/protocol-overview |

### cursor:1.1.6

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://agentclientprotocol-typescript-sdk.mintlify.app/clients/handling-updates |
| primary | B3 | T2 | — † | — | cur | — | https://agentclientprotocol.com/protocol/v2/tool-calls |
| research | B3 | T3 | — † | — | cur | — | https://cecli.dev/docs/config/api/ |

### cursor:1.2.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/mastra-ai/mastra/pull/18876 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/mastra-ai/mastra/blob/64a4f3e9/packages/core/src/workflows/evented/workflow.ts |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/mastra-ai/mastra/blob/a7bbe773/packages/core/src/events/pubsub.ts |
| primary | B3 | T2 | — † | — | cur | — | https://mastra.ai/reference/pubsub/base |
| research | B3 | T3 | — † | — | cur | — | https://docs.rs/assay-workflow/latest/src/assay_workflow/ctx.rs.html |

### cursor:1.5.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://docs.rs/axocoatl-server/latest/axocoatl_server/routes/fn.a2a_receive_task.html |
| research | B3 | T3 | — † | — | cur | — | https://github.com/myles1663/lancelot/blob/master/docs/a2a.md |

### cursor:2.2.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/vellaveto-server/latest/src/vellaveto_server/policy_lifecycle.rs.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.sequencemkts.com/cli/bundles/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.styra.com/das/policies/bundles/using-bundle-promotion |
| primary | B3 | T2 | — † | — | cur | — | https://docs.styra.com/das/policies/bundles/bundle-registry |
| primary | B3 | T2 | — † | — | cur | — | https://git.stella-ops.org/stella-ops.org/git.stella-ops.org/raw/branch/main/docs/flows/14-multi-tenant-policy-rollout-flow.md |

### cursor:2.3.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/prnvh/plancompiler |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/agentspan-ai/agentspan/pull/238 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/zynax-io/zynax/issues/101 |
| research | B2 | T3 | 2026-04 | url | cur | — | https://arxiv.org/html/2604.13092v1 |
| research | B3 | T3 | 2025-11 | url | cur | — | https://doi.org/10.48550/arxiv.2511.03094 |

### cursor:2.3.6

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/nibzard/awesome-agentic-patterns/blob/main/patterns/planner-worker-separation-for-long-running-agents.md |
| research | B1 | T3 | 2026-07 | url | cur | — | https://jigarjoshi.in/blog/cursor-agent-swarm-planner-worker-routing-july-2026/ |
| research | B2 | T3 | 2026 | url | cur | — | https://tokenkarma.app/blog/cursor-agent-swarm-cost-economics-2026/ |
| research | B3 | T3 | — † | — | cur | — | https://chatgpt.ca/blog/multi-model-ai-planner-worker-cost |
| research | B3 | T3 | — † | — | cur | — | https://www.digitalapplied.com/blog/cursor-agent-swarm-sqlite-rust-planner-worker-economics |

### cursor:2.4.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | 2024-07 | url | cur | — | https://doc.dpdk.org/guides-24.07/prog_guide/qos_framework.html |
| primary | B3 | T2 | 2024-03 | url | cur | — | http://doc.dpdk.org/guides-24.03/prog_guide/qos_framework.html |
| primary | B3 | T2 | — † | — | cur | — | https://doc.dpdk.org/api-23.11/rte__sched_8h.html |
| primary | B3 | T2 | — † | — | cur | — | https://doc.dpdk.org/guides/prog_guide/ethdev/qos_framework.html |
| primary | B3 | T2 | — † | — | cur | — | https://doc.dpdk.org/api/rte__sched_8h.html |

### cursor:2.4.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.temporal.io/design-patterns/downstream-rate-limiting |
| primary | B3 | T2 | — † | — | cur | — | https://docs.temporal.io/guides/rate-limit-downstream-apis |
| primary | B3 | T2 | — † | — | cur | — | https://www.inngest.com/blog/how-durable-workflow-engines-work |
| primary | B3 | T2 | — † | — | cur | — | https://www.inngest.com/docs/guides/throttling |
| research | B3 | T3 | — † | — | cur | — | https://robulka.com/durable-execution/ |

### cursor:2.4.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://kueue.sigs.k8s.io/docs/concepts/fair_sharing/ |
| core | B3 | T1 | — † | — | cur | — | https://kueue.sigs.k8s.io/docs/concepts/admission_fair_sharing/ |
| core | B3 | T1 | — † | — | cur | — | https://kueue.sigs.k8s.io/v0.17/docs/concepts/preemption/ |
| core | B3 | T1 | — † | — | cur | — | https://kueue.sigs.k8s.io/docs/concepts/cluster_queue/ |
| research | B3 | T3 | 2025-08 | url | cur | — | https://arxiv.org/html/2508.16646 |

### cursor:2.4.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://www.corpay.com/resources/blog/schedule-of-values |
| research | B3 | T3 | — † | — | cur | — | https://crewcost.com/blog/construction-schedule-of-works/ |
| research | B3 | T3 | — † | — | cur | — | https://getbuilt.com/blog/schedule-of-values-in-construction/ |
| research | B3 | T3 | — † | — | cur | — | https://www.procore.com/library/schedule-of-values-explained |
| research | B3 | T3 | — † | — | cur | — | https://projectmanagementformula.com/schedule-of-works/ |

### cursor:2.5.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/crate/durable-workflow/2.0.0-rc.32 |
| primary | B3 | T2 | — † | — | cur | — | https://docs.workflowengine.io/get-started/concepts/workflow-runtime/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ablative-io/aion/blob/main/docs/design/workflow-engine/COMPONENT-ARCHITECTURE.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/solutionforest/workflow-engine-core/ |

### cursor:2.5.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/serverlessworkflow/specification/blob/0.8.x/specification.md |
| primary | B3 | T2 | — † | — | cur | — | https://docs.camunda.io/docs/guides/migrating-from-camunda-7/ |
| primary | B3 | T2 | — † | — | cur | — | https://unsupported.docs.camunda.io/8.2/docs/guides/migrating-from-camunda-7/migration-readiness/ |
| research | B3 | T3 | — † | — | cur | — | https://www.jointjs.com/blog/bpmn-modeling-vs-execution |

### cursor:2.5.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.aws.amazon.com/durable-execution/getting-started/key-concepts/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/agent-framework-core/latest/src/agent_framework_core/workflow/shared_state.rs.html |
| primary | B3 | T2 | — † | — | cur | — | https://docs.workflowengine.io/evaluate/workflow-engine-features/durable-execution/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/Raizo-TCS/phronomy/blob/main/docs/runtime-and-concurrency.md |
| primary | B3 | T2 | — † | — | cur | — | https://stately.ai/docs/xstate/v6/durable-execution |

### cursor:2.5.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://corvid-lang.org/docs/internals/effect-spec/14-replay |
| research | B2 | T3 | 2026-04-12 | url | cur | — | https://tianpan.co/blog/2026/04/12/write-ahead-logging-for-ai-agents-crash-safe-execution |
| research | B3 | T3 | — † | — | cur | — | https://news.lavx.hu/article/the-execution-guard-pattern-for-ai-agents |

### cursor:2.6.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://agentgateway.dev/docs/kubernetes/latest/agent/a2a/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.docker.com/ai/docker-agent/tools/handoff/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.inkeep.com/talk-to-your-agents/a2a |
| primary | B3 | T2 | — † | — | cur | — | https://learn.microsoft.com/en-us/agent-framework/journey/agent-to-agent |
| research | B3 | T3 | — † | — | cur | — | https://stacka2a.dev/blog/a2a-kubernetes-deployment-guide |

### cursor:2.6.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://developers.cloudflare.com/ai-gateway/features/dynamic-routing/index.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/NVIDIA-NeMo/Switchyard/blob/main/docs/routing_algorithms/overview.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/routatic/proxy/blob/main/docs/howto-custom-routing.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/alenisaw/routis |
| primary | B3 | T2 | — † | — | cur | — | https://gitlab.com/pilotphp/http/-/tree/main |

### cursor:2.6.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/microsoft/agent-framework/blob/main/python/packages/orchestrations/README.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/microsoft/agent-framework/blob/e39a8a2e/python/packages/orchestrations/agent_framework_orchestrations/_handoff.py |
| research | B3 | T3 | — † | — | cur | — | https://agentpatterns.ai/patterns/agent-design/agent-composition-patterns/ |
| research | B3 | T3 | — † | — | cur | — | https://gainam.com/insights/multi-agent-orchestration-patterns |
| research | B3 | T3 | — † | — | cur | — | https://multi-agent.wiki/patterns |

### cursor:2.6.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/initorigin/io-harness/blob/main/docs/guide/composition.md |
| primary | B3 | T2 | — † | — | cur | — | https://mintlify.wiki/burkeholland/max/concepts/architecture |
| primary | B3 | T2 | — † | — | cur | — | https://mintlify.wiki/burkeholland/max/concepts/workers |
| primary | B3 | T2 | — † | — | cur | — | https://mintlify.wiki/burkeholland/max/concepts/orchestrator |
| research | B3 | T3 | — † | — | cur | — | https://levelup.gitconnected.com/the-orchestrator-worker-pattern-how-to-structure-a-multi-agent-system-58d469a8e5e1 |

### cursor:3.1.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-how-it-works.html |
| primary | B2 | T2 | 2026-06 | age | cur | — | https://deepseek-harness.github.io/deepseek-harness/en/reference/subsystems/jobs |
| research | B1 | T3 | 2026-08 | age | cur | — | https://thenewstack.io/agent-session-aware-runtime/ |
| research | B1 | T3 | 2026-07 | age | cur | — | https://deepwiki.com/AgentBull/ankole/2.2-actor-runtime-and-worker-pool |

### cursor:3.2.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://agentgateway.dev/docs/standalone/latest/documentation/llm/cost-controls/costs/ |
| research | B1 | T3 | 2026-08 | age | cur | — | https://www.solo.io/blog/building-real-time-ai-cost-controls-with-agentgateway |
| research | B1 | T3 | 2026-07 | age | cur | — | https://mdsanwarhossain.me/blog-llm-gateway-production.html |
| research | B2 | T3 | 2026-06 | age | cur | — | https://terminalskills.io/use-cases/build-llm-gateway-with-fallback-and-cost-control |
| research | B3 | T3 | — † | — | cur | — | https://www.gravitee.io/blog/how-ai-analytics-is-transforming-data-processing-agents-tokens-and-beyond |

### cursor:3.2.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://agentgateway.dev/docs/kubernetes/main/documentation/llm/failover/ |
| primary | B1 | T2 | 2026-08 | age | cur | — | https://agentgateway.dev/docs/kubernetes/latest/security/rate-limit-http |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://agentgateway.dev/docs/standalone/latest/documentation/configuration/resiliency/retries/ |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://agentgateway.dev/docs/standalone/latest/documentation/configuration/resiliency/rate-limits/ |

### cursor:3.3.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-08 | age | cur | — | https://agentproto.sh/docs/aip-36 |
| primary | B1 | T2 | 2026-08 | age | cur | — | https://www.anthropic.com/engineering/claude-code-sandboxing |
| primary | B1 | T2 | 2026-07 | url | cur | — | https://github.com/agentproto/agentproto/blob/main/specs/aip-36.mdx |
| primary | B1 | T2 | 2026-07 | url | cur | — | https://github.com/anthropics/sandbox-runtime |

### cursor:3.3.6

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://docs.docker.com/ai/sandboxes/security/isolation/ |
| primary | B1 | T2 | 2026-07 | age | cur | — | https://agent-sandbox.sigs.k8s.io/docs/use-cases/examples/nono-sandbox/ |
| research | B1 | T3 | 2026-08 | url | cur | — | https://github.com/NousResearch/hermes-agent/pull/94878 |
| research | B2 | T3 | 2026-06 | age | cur | — | https://developer.nvidia.com/blog/practical-security-guidance-for-sandboxing-agentic-workflows-and-managing-execution-risk/ |
| research | B2 | T3 | 2026-06 | age | cur | — | https://www.truefoundry.com/blog/sandboxed-code-agents-secure-execution |

### cursor:3.4.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08 | age | cur | — | https://mitos.run/docs/workspaces |
| research | B1 | T3 | 2026-07 | age | cur | — | https://kla.digital/platform/execution-lineage |
| research | B2 | T3 | 2026-06 | age | cur | — | https://omnithium.ai/platform/ |
| research | B3 | T3 | — † | — | cur | — | https://github.com/avartan-labs/hetu |
| research | B3 | T3 | — † | — | cur | — | https://github.com/chernistry/bernstein/ |

### cursor:3.4.6

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B2 | T2 | 2026-06 | age | cur | — | https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot |
| primary | B2 | T2 | 2026-06 | url | cur | — | https://github.com/microsoft/vscode-copilot-chat/blob/main/assets/prompts/skills/agent-customization/references/workspace-instructions.md |
| research | B1 | T3 | 2026-08 | age | cur | — | https://ctxwire.com/articles/debug-agent-instruction-conflicts/ |

### cursor:3.5.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-08 | url | cur | — | https://github.com/modelcontextprotocol/registry/blob/main/docs/modelcontextprotocol-io/about.mdx |
| core | B1 | T1 | 2026-08 | age | cur | — | https://modelcontextprotocol.io/registry/about.md |
| core | B1 | T1 | 2026-07 | url | cur | — | https://raw.githubusercontent.com/modelcontextprotocol/registry/refs/heads/main/docs/reference/server-json/generic-server-json.md |
| core | B2 | T1 | 2026-06 | url | cur | — | https://github.com/modelcontextprotocol/registry/tree/3c42f68750e941f4e052f08cd71dbc475a9b815c/docs/server-json |

### cursor:4.1.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://learning.sap.com/courses/sap-successfactors-platform-advanced-and-talent-intelligence-hub-academy/overview-and-enablement-of-job-profile-builder-jbp_b9b6d506-02b7-47ac-88a4-0b121fb86a38 |
| primary | B3 | T2 | — † | — | cur | — | https://learning.sap.com/courses/sap-successfactors-platform-advanced-and-talent-intelligence-hub-academy-es/managing-job-architecture-with-job-profile-builder-jpb |
| primary | B3 | T2 | — † | — | cur | — | https://userapps.support.sap.com/sap/support/knowledge/en/2832345 |
| primary | B3 | T2 | — † | — | cur | — | https://userapps.support.sap.com/sap/support/knowledge/en/2419515 |

### cursor:4.1.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/kubernetes/kubernetes/blob/master/pkg/scheduler/apis/config/types.go |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/kubernetes/enhancements/blob/master/keps/sig-scheduling/785-scheduler-component-config-api/README.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/kubernetes/enhancements/blob/master/keps/sig-scheduling/1451-multi-scheduling-profiles/README.md |
| primary | B3 | T2 | — † | — | cur | — | https://kubernetes.io/docs/reference/scheduling/config/ |
| research | B2 | T3 | 2026-02-09 | url | cur | — | https://oneuptime.com/blog/post/2026-02-09-multiple-scheduler-profiles-plugins/view |

### cursor:4.2.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://agent-sandbox.sigs.k8s.io/docs/use-cases/anthropic-managed-agents/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.cloud.google.com/kubernetes-engine/docs/how-to/provisioningrequest |
| primary | B3 | T2 | — † | — | cur | — | https://gateway-api-inference-extension.sigs.k8s.io/api-types/inferencepool/ |
| primary | B3 | T2 | — † | — | cur | — | https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/ |

### cursor:4.4.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/eidentic/eidentic/blob/main/docs/design/15-data-governance.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/jkelly-dev1/ai-data-boundary-proxy |
| research | B3 | T3 | — † | — | cur | — | https://www.c-sharpcorner.com/article/architecting-gdpr-compliant-genai-an-end-to-end-guide-to-multi-agent-rag-with-l/ |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/pablets/pii-that-can-actually-be-forgotten-blind-indexes-and-crypto-shredding-in-an-ai-agent-stack-5b4g |
| WILD | B3 | U | — † | — | cur | — | https://tomevault.io/tome/peterbamuhigire/skills-web-dev/ai-agent-memory-erasure-proof |

### cursor:4.4.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/ai-memory/latest/ai_memory/handlers/links/fn.get_lineage.html |
| primary | B3 | T2 | — † | — | cur | — | https://www.hippocortex.dev/docs/enterprise/LINEAGE |
| research | B2 | T3 | 2026-05 | url | cur | — | https://arxiv.org/pdf/2605.14421 |
| research | B2 | T3 | 2026-05 | url | cur | — | https://arxiv.org/html/2605.14421 |
| research | B2 | T3 | 2026-05 | url | cur | — | https://doi.org/10.48550/arxiv.2605.14421 |

### cursor:5.1.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://coderlegion.com/23384/never-let-an-ai-agent-grade-its-own-homework |
| research | B3 | T3 | — † | — | cur | — | https://www.critique.sh/blog/agents-grade-their-own-homework |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/dbsoul/the-independent-auditor-pattern-dont-let-the-thing-that-built-it-verify-it-4bbo |
| research | B3 | T3 | — † | — | cur | — | https://ienable.ai/blog/why-ai-agents-should-never-grade-their-own-homework.html |
| research | B3 | T3 | — † | — | cur | — | https://nhimg.org/faq/what-do-security-teams-get-wrong-about-verify-steps-in-agent-workflows/ |

### cursor:6.1.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/registry/attributes/gen-ai.md |
| primary | B3 | T2 | — † | — | cur | — | https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation-genai/openai.html |
| research | B1 | T3 | 2026-07-09 | exc | cur | — | https://pypi.org/project/opentelemetry-util-genai/ |

### cursor:6.1.6

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | 2024-07 | url | cur | — | https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse |
| research | B3 | T3 | — † | — | cur | — | https://www.honeycomb.io/blog/instrumenting-ai-agents-agent-timeline-opentelemetry-guide |
| research | B3 | T3 | — † | — | cur | — | https://www.honeycomb.io/resources/getting-started/agent-observability |
| research | B3 | T3 | — † | — | cur | — | https://meshai.dev/observability |

### cursor:6.2.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B2 | T3 | 2026-06 | exc | cur | — | https://www.alphaxiv.org/abs/2606.14516 |
| research | B2 | T3 | 2026-06 | exc | cur | — | https://arxiv.org/html/2606.14516v1 |
| research | B2 | T3 | 2026-06 | exc | cur | — | https://doi.org/10.48550/arxiv.2606.14516 |
| research | B3 | T3 | — † | — | cur | — | https://blog.mozilla.ai/lets-build-an-app-for-evaluating-llms/ |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/agentoperations/agent-registry/2.3-storage-layer |
| research | B3 | T3 | — † | — | cur | — | https://exesolution.com/solutions/spring-boot-llm-eval-harness-ci-regression |
| research | B3 | T3 | — † | — | cur | — | https://github.com/swarm-ai-research/swarm-artifacts/blob/main/RESEARCH_OS_SPEC.md |
| research | B3 | T3 | — † | — | cur | — | https://github.com/evaleval/every_eval_ever |
| research | B3 | T3 | — † | — | cur | — | https://leetllm.com/learn/deep-dive-mlflow |

### cursor:6.2.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.langchain.com/langsmith/attach-user-feedback |
| primary | B3 | T2 | — † | — | cur | — | https://langfuse.com/guides/user-feedback-loop |
| primary | B3 | T2 | — † | — | cur | — | https://mastra.ai/docs/observability/feedback |

### cursor:7.1.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B1 | T2 | 2026-08-14 | exc | cur | — | https://github.com/microsoft/agent-framework/issues/6328 |
| primary | B1 | T2 | 2026-08-02 | exc | cur | — | https://github.com/microsoft/agent-framework/issues/6240 |
| primary | B1 | T2 | 2026-07-25 | exc | cur | — | https://github.com/microsoft/agent-framework/blob/be8d2619/python/packages/orchestrations/agent_framework_orchestrations/_handoff.py |
| research | B1 | T3 | 2026-08-28 | url | cur | — | https://arxiv.org/pdf/2608.24358 |
| research | B2 | T3 | 2026-05-19 | exc | cur | — | https://github.com/dunetrace/dunetrace/issues/20 |

### cursor:8.1.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/agentconnect-md/agentconnect/blob/2671ed6b/packages/daemon/src/workspace/workspace-manager.ts |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/knownothing20/mcp-remote-agent |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/knownothing20/AgentPort |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/knownothing20/AgentPort/blob/main/AGENT_GUIDE.md |
| WILD | B3 | U | — † | — | cur | — | https://deepwiki.com/agentconnect-md/agentconnect/4.5-workspace-management |

### cursor:8.2.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://atlan.com/know/data-retention-policy-framework/ |
| research | B3 | T3 | — † | — | cur | — | https://captaincompliance.com/education/data-retention-policy-what-it-is-legal-requirements-best-practices/ |
| research | B3 | T3 | — † | — | cur | — | https://infinisynapse.com/en/blog/what-is-a-data-retention-policy |
| research | B3 | T3 | — † | — | cur | — | https://www.talarity.com/resources/education/data-retention-settings |
| research | B3 | T3 | — † | — | cur | — | https://umbrex.com/resources/data-governance-playbook/data-classification-retention-and-records-alignment/ |

### cursor:8.2.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://buckets.hexdocs.pm/Buckets.Cloud.html |
| primary | B3 | T2 | — † | — | cur | — | https://buckets.hexdocs.pm/Buckets.html |
| primary | B3 | T2 | — † | — | cur | — | https://buckets.hexdocs.pm/Buckets.Cloud.Dynamic.html |
| primary | B3 | T2 | — † | — | cur | — | https://buckets.hexdocs.pm/multi-cloud-setup.html |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/elixir-saas/buckets/blob/master/README.md |

### cursor:8.3.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://quelvio.com/blog/permission-aware-retrieval |
| research | B1 | T3 | 2026-07-18 | url | cur | — | https://www.simplico.net/2026/07/18/rag-retrieval-layer-access-control/ |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/venkathub/permission-aware-rag-enforcing-document-acls-at-retrieval-time-54a7 |
| research | B3 | T3 | — † | — | cur | — | https://doi.org/10.71097/ijaidr.v17.i1.2041 |

### cursor:8.5.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/opencontainers/image-spec/blob/5d055a4805219e3ebf7ed740622e38b57d36d3a0/artifact.md |
| core | B3 | T1 | — † | — | cur | — | https://github.com/opencontainers/artifacts/blob/a56aaad3afb5bab321644e3508f76d915031b3da/artifact-manifest/artifact-manifest.md |
| core | B3 | T1 | — † | — | cur | — | https://github.com/opencontainers/artifacts/blob/main/artifact-authors.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/agentoperations/agent-registry |

### cursor:9.1.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-20 | exc | cur | cursor:9.1.2 | https://agentclientprotocol.com/announcements/acp-v2-draft |
| core | B3 | T1 | — † | — | cur | — | https://agentclientprotocol.com/rfds/v2/overview |
| core | B3 | T1 | — † | — | cur | — | https://agentclientprotocol.com/rfds/about |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/agentclientprotocol/agent-client-protocol/7.1-rfd-process |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/agentclientprotocol/agent-client-protocol/8.5-contributing-guidelines |
| research | B3 | T3 | — † | — | cur | — | https://github.com/agentclientprotocol/agent-client-protocol/blob/c50e1cd2/docs/rfds/introduce-rfd-process.mdx |

### cursor:9.1.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/agentclientprotocol/agent-client-protocol/7-rfds-and-protocol-evolution |

### cursor:9.1.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://agentclientprotocol-typescript-sdk.mintlify.app/agents/session-management |
| primary | B3 | T2 | — † | — | cur | cursor:9.1.5 | https://agentclientprotocol.github.io/rust-sdk/protocol.html |
| primary | B3 | T2 | — † | — | cur | — | https://agentclientprotocol.github.io/symposium-acp/mcp-bridge.html |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/agentclientprotocol/agent-client-protocol/2.4.2-session-management |

### cursor:9.1.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://agentclientprotocol.com/protocol/v2/extensibility |
| core | B3 | T1 | — † | — | cur | — | https://agentclientprotocol.com/rfds/v2/enum-variant-extension |
| core | B3 | T1 | — † | — | cur | — | https://agentclientprotocol.com/protocol/v1/extensibility |
| primary | B3 | T2 | — † | — | cur | — | https://agentclientprotocol-typescript-sdk.mintlify.app/advanced/extension-methods |
| primary | B3 | T2 | — † | — | cur | — | https://docs.rs/agent-client-protocol/latest/agent_client_protocol/schema/v2/struct.ExtRequest.html |

### cursor:9.1.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://agentclientprotocol.com/protocol/v1/overview |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/djasdh/hermes-acp-http |
| primary | B3 | T2 | — † | — | cur | — | https://www.npmjs.com/package/adapter-acp |

### cursor:9.1.6

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | 2025-08 | exc | cur | — | https://www.katonic.ai/blog/agent-protocols |
| research | B3 | T3 | — † | — | cur | — | https://4sysops.com/archives/comparing-ai-protocols-mcp-a2a-agp-agntcy-ibm-acp-zed-acp/ |
| research | B3 | T3 | — † | — | cur | — | https://circleci.com/blog/acp-vs-mcp-whats-the-difference-for-agentic-coding/ |
| WILD | B3 | U | — † | — | cur | — | https://news.ycombinator.com/item?id=45074147 |

### cursor:9.2.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://docs.ag-ui.com/drafts/overview |
| primary | B1 | T2 | 2026-08-27 | age | cur | — | https://www.npmjs.com/package/@ag-ui/client |
| primary | B1 | T2 | 2026-08-27 | age | cur | cursor:9.2.2 | https://registry.npmjs.org/%40ag-ui%2Fcore |
| primary | B1 | T2 | 2026-06-24 | exc | cur | — | https://github.com/ag-ui-protocol/ag-ui/tree/455892c2a01db1130512669e7220845a26df6457 |
| primary | B3 | T2 | — † | — | cur | — | https://docs.copilotkit.ai/ag-ui |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ag-ui-protocol/ag-ui/blob/7890075f/docs/introduction.mdx |
| research | B3 | T3 | — † | — | cur | — | https://registry.npmjs.org/ag-ui-validate/-/ag-ui-validate-0.4.0.tgz |

### cursor:9.2.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.ag-ui.com/ |
| primary | B3 | T2 | — † | — | cur | — | https://docs.copilotkit.ai/ag-ui/introduction |
| research | B2 | T3 | 2026-03 | exc | cur | — | https://rywalker.com/research/ag-ui |

### cursor:9.2.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.ag-ui.com/sdk/python/core/types |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ag-ui-protocol/ag-ui/blob/677dfca1/integrations/adk-middleware/python/USAGE.md |

### cursor:9.2.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://docs.ag-ui.com/concepts/metadata |
| primary | B3 | T2 | — † | — | cur | — | https://docs.ag-ui.com/sdk/js/core/types |

### cursor:9.2.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://dev.umodoc.com/en/docs/next/ai/troubleshooting |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ag-ui-protocol/ag-ui/blob/821b8c227c6fe7b78de2c8259173dd7cbbdf181b/sdks/dotnet/plugins/ag-ui-dotnet/skills/agui-dotnet-troubleshoot/SKILL.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ag-ui-protocol/ag-ui/issues/2306 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/ag-ui-protocol/ag-ui/blob/677dfca1/skills/ag-ui-a2ui-integration/references/framework-adapters.md |
| primary | B3 | T2 | — † | — | cur | — | https://threadplane.ai/docs/ag-ui/guides/troubleshooting |

### cursor:9.3.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B2 | T1 | 2026-03-12 | exc | cur | cursor:9.3.2 | https://a2a-protocol.org/latest/blog/2026/03/12/a2a-protocol-ships-v10-production-ready-standard-for-agent-to-agent-communication/ |
| core | B2 | T1 | 2026-03-12 | exc | cur | cursor:9.3.2 | https://a2a-protocol.org/v1.0.0/announcing-1.0/ |
| primary | B2 | T2 | 2026-01-14 | url | cur | cursor:9.3.5 | https://github.com/a2aproject/A2A/commit/a4afeea788b3877101f7a63c2e50091709490058 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/a2aproject/A2A/pull/1882 |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/a2aproject/a2a-tck/blob/main/docs/SPEC_UPDATE_WORKFLOW.md |
| research | B3 | T3 | — † | — | cur | — | https://github.com/TJC-LP/scalagent/commit/000d8448d2a4465574f546f728ea1b00b3a6131b |

### cursor:9.3.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-06-23 | exc | cur | — | https://developers.googleblog.com/google-cloud-donates-a2a-to-linux-foundation/ |
| research | B3 | T3 | — † | — | cur | — | https://agent2agent.info/docs/community/whats-new-v1/ |

### cursor:9.3.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | cursor:9.4.3 | https://www.agentcard.net/blog/a2a-vs-mcp |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/vahapogut/how-i-built-a-universal-mcp-a2a-bridge-architecture-protocol-mapping-and-what-i-learned-df3 |
| research | B3 | T3 | — † | — | cur | cursor:9.4.3 | https://dzone.com/articles/how-ai-agents-communicate |
| research | B3 | T3 | — † | — | cur | — | https://github.com/naveenkumarbaskaran/mcp-a2a-bridge |
| research | B3 | T3 | — † | — | cur | — | https://github.com/aarushitandon0/a2a-mcp-bridge |
| research | B3 | T3 | — † | — | cur | — | https://github.com/reaatech/a2a-reference-ts/blob/main/docs/bridge-deep-dive.md |
| research | B3 | T3 | — † | — | cur | — | https://github.com/ytugarev/a2a-mcp-bridge |

### cursor:9.3.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/a2aproject/A2A/blob/main/docs/topics/extension-and-binding-governance.md |

### cursor:9.3.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/a2aproject/a2a-js/blob/main/docs/compatibility-v0_3.md |
| research | B3 | T3 | — † | — | cur | — | https://github.com/a2aproject/A2A/issues/1755 |
| research | B3 | T3 | — † | — | cur | — | https://mortalapps.com/agents/protocols/a2a-backward-compatibility/ |

### cursor:9.4.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B1 | T1 | 2026-07-28 | exc | cur | cursor:9.4.2 | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/blog/content/posts/2026-07-28-spec-ga/index.md |
| core | B3 | T1 | 2025-12 | exc | cur | cursor:9.4.2 | https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation |
| core | B3 | T1 | — † | — | cur | cursor:9.4.2 | https://modelcontextprotocol.io/seps/2484-conformance-tests-required-for-final-seps |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/modelcontextprotocol/conformance/blob/main/README.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/modelcontextprotocol/conformance/blob/main/SDK_INTEGRATION.md |

### cursor:9.4.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://colrows.com/blogs/mcp-enterprise-adoption/ |
| research | B3 | T3 | — † | — | cur | — | https://ppc.land/mcp-forces-ad-tech-to-rebuild-agent-servers-as-sessions-disappear/ |

### cursor:9.4.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://github.com/prefrontalsys/mcacp |
| research | B3 | T3 | — † | — | cur | — | https://mcp.aibase.com/server/1639703093849629255 |

### cursor:9.4.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | — † | — | cur | — | https://github.com/modelcontextprotocol/modelcontextprotocol/blob/ff960c9e/seps/2133-extensions.md |
| core | B3 | T1 | — † | — | cur | — | https://modelcontextprotocol.io/seps/2133-extensions |
| primary | B3 | T2 | — † | — | cur | — | https://py.sdk.modelcontextprotocol.io/v2/advanced/extensions/ |
| primary | B3 | T2 | — † | — | cur | — | https://py.sdk.modelcontextprotocol.io/api/mcp/shared/extension/ |

### cursor:9.4.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://fast-agent.ai/mcp/client-servers/ |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/leehack/mcp_dart/blob/main/doc/mcp-2026-07-28.md |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/WordPress/mcp-adapter/issues/131 |
| research | B1 | T3 | 2026-08 | age | cur | — | https://startdebugging.net/2026/08/fix-mcp-unsupported-protocol-version-2025-11-25-vs-2026-07-28/ |

### cursor:9.5.1

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2025-12 | exc | cur | cursor:9.5.2 | https://aaif.io/news/linux-foundation-announces-formation-of-aaif |
| core | B3 | T1 | 2025-12 | exc | cur | cursor:9.5.2 | https://openai.com/index/agentic-ai-foundation/ |
| research | B3 | T3 | — † | — | cur | cursor:9.5.4 | https://deepwiki.com/agentsmd/agents.md/7-agents.md-specification |

### cursor:9.5.2

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B1 | T3 | 2026-07-19 | url | cur | — | https://codex.danielvaughan.com/2026/07/19/agents-md-maturity-curve-evolution-project-context-codex-cli/ |

### cursor:9.5.3

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://github.com/voxmedia/open-agent-toolkit/blob/main/.agents/docs/rules-files.md |
| research | B2 | T3 | 2026 | age | cur | — | https://codersera.com/blog/agents-md-vs-claude-md-vs-cursor-rules-comparison-2026/ |
| research | B3 | T3 | — † | — | cur | — | https://fp8.co/articles/AGENTS-md-vs-CLAUDE-md-vs-Cursor-Rules-Agent-Instruction-Files |
| research | B3 | T3 | — † | — | cur | — | https://getunblocked.com/blog/claude-md-vs-agents-md-vs-cursor-rules/ |

### cursor:9.5.4

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://github.com/sno-ai/mda/blob/main/spec/v1.0/06-targets/agents-md.md |
| research | B3 | T3 | — † | — | cur | — | https://github.com/cloudflare/agent-skills-discovery-rfc/issues/9 |
| research | B3 | T3 | — † | — | cur | — | https://thepromptshelf.dev/blog/agents-md-best-practices/ |

### cursor:9.5.5

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| research | B3 | T3 | — † | — | cur | — | https://dev.to/agentbriefstudio/7-reasons-coding-agents-ignore-your-agentsmd-and-how-to-fix-them-jao |
| WILD | B3 | U | — † | — | cur | — | https://www.youtube.com/watch?v=4rLJmg9-zow |

### cursor:U.0

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| core | B3 | T1 | 2022-11-07 | age | cur | — | https://standards.ieee.org/ieee/42010/6846/ |
| core | B3 | T1 | — † | — | cur | — | https://ieeexplore.ieee.org/iel7/9938424/9938445/09938446.pdf |
| core | B3 | T1 | — † | — | cur | — | https://www.iso.org/standard/74393.html |
| core | B3 | T1 | — † | — | cur | — | https://www.iso.org/obp/ui/#iso:std:iso-iec-ieee:42010:ed-2:v1:en:term:3.13 |
| core | B3 | T1 | — † | — | cur | — | https://www.iso.org/standard/50508.html |
| research | B1 | T3 | 2026-08 | age | cur | — | https://quality.arc42.org/standards/iso-42010 |
| research | B1 | T3 | 2026-08-19 | age | cur | — | https://javapro.io/2026/08/19/hexagonal-architecture-for-machine-learning-ports-adapters-and-model-versioning-in-spring-boot/ |
| research | B2 | T3 | 2026-01-24 | exc | cur | — | https://docs.rs/crate/queue-runtime/latest/source/docs/adr/ADR-001-hexagonal-architecture.md |
| research | B3 | T3 | 2024-01 | url | cur | — | https://arxiv.org/pdf/2401.12011 |
| WILD | B2 | U | 2026-06-01 | exc | cur | — | https://github.com/phuthuycoding/moicle/pull/5 |
| WILD | B2 | U | 2026-05-29 | age | cur | — | https://blog.pacificcert.com/iso-42010-architecture-descriptions-systems-software/ |
| WILD | B2 | U | 2026-04-05 | exc | cur | — | https://github.com/ducpm2303/claude-java-plugins/pull/5 |
| WILD | B3 | U | 2025-10-01 | age | cur | — | https://johal.in/hexagonal-architecture-design-python-ports-and-adapters-for-modularity-2026/ |

### cursor:U.9

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.controlzero.ai/docs/concepts/enforcement-behavior |
| research | B3 | T3 | — † | — | cur | — | https://agenticdevelopercookbook.com/guidelines/planning/code-quality/cross-cutting-detection |
| research | B3 | T3 | — † | — | cur | — | https://www.arcade.dev/blog/one-question-every-tool-call |
| research | B3 | T3 | — † | — | cur | — | https://deepwiki.com/zeroclaw-labs/zeroclaw/5.1-security-policy-and-enforcement |
| WILD | B3 | U | — † | — | cur | — | https://github.com/databricks-solutions/consort/blob/main/skills/software-design-principles/references/cross-cutting-concerns.md |

### cursor:U.11

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://docs.orxhestra.com/composer/overview |
| primary | B3 | T2 | — † | — | cur | — | https://leithdocs.com/plumbing/ |
| research | B3 | T3 | — † | — | cur | — | https://dev.to/htekdev/the-functional-options-pattern-for-ai-agent-composition-15of |

### cursor:U.12

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://developer.box.com/guides/authentication/client-credentials |
| primary | B3 | T2 | — † | — | cur | — | https://developer.box.com/guides/authentication/client-credentials/client-credentials-setup |
| primary | B3 | T2 | — † | — | cur | — | https://developer.box.com/guides/api-calls/permissions-and-errors/scopes |
| primary | B3 | T2 | — † | — | cur | — | https://github.com/box/developer.box.com/blob/main/content/guides/embed/ui-elements/access.md |
| research | B2 | T3 | 2026-05-28 | exc | cur | — | https://www.sourcingspeak.com/mcp-toolkit-contract-terms-deployment/ |

### cursor:U.13

**Q:** (v1 question, no v2.0 counterpart)

| Trust | Bucket | Tier | Date | Src | Models | Also | URL |
|---|---|---|---|---|---|---|---|
| primary | B3 | T2 | — † | — | cur | — | https://agent-box.sh/docs/api |
| primary | B3 | T2 | — † | — | cur | — | https://agent-box.sh/docs/environment |
| primary | B3 | T2 | — † | — | cur | — | https://agent-box.sh/docs/teleport-a-project |
| primary | B3 | T2 | — † | — | cur | — | https://crabbox.sh/how-it-works.html |
| WILD | B3 | U | — † | — | cur | — | https://github.com/madarco/agentbox/blob/main/docs/control-plane-guide.md |

