# Verifier brief (STATUS rows 67 and 68): re-answer a sample without seeing the crew's answers

You are the honesty check on an answer set. You are given a list of question ids and nothing the crew wrote; the crew's answer files are not in your checkout. Answer each sampled question exactly as the crew brief for that instrument says (state/briefs/litmus-answer.md for the litmus questionnaire, state/briefs/conformance-answer.md for the conformance questionnaire), with the same evidence rules, into the file your launch message names. Do not commit, push or ledger. Do not open any file under docs/litmus/answers or full-stack-questionair/answers.

Your label is `<row>-spot-check`. Run the instrument's checker on your file until it prints 0 errors. Reply in under 60 words: how many answered, counts by score or verdict.
