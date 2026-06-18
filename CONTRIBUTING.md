# Contributing to robotframework-vitro

Thanks for your interest in contributing. This project is a thin Robot Framework
bridge for the vitro test framework, and we ask every contributor to sign off on
the Developer Certificate of Origin (DCO) for the work they submit.

## Developer Certificate of Origin (DCO)

To keep the project legally safe and permanently open source, we use the
[Developer Certificate of Origin](https://developercertificate.org/) (DCO) —
the same lightweight process used by the Linux kernel, Git, and Docker. There
is no separate agreement to sign and nothing to email.

The DCO is a statement that you wrote the contribution (or otherwise have the
right to submit it) and that you agree to license it under the project's
inbound license, **Apache-2.0**. Inbound equals outbound: your contributions
are offered under the same terms as the project itself, which keeps the code
open source and the provenance clear. You retain copyright in your work.

### How to sign your work

Add a `Signed-off-by` line to each commit message, using your real name and an
email you can be reached at:

```text
This is my commit message

Signed-off-by: Jane Doe <jane.doe@example.com>
```

Git can add this for you — just pass the `-s` / `--signoff` flag when you
commit:

```bash
git commit -s -m "Your message"
```

By adding the sign-off you certify the statements in the DCO. **Every commit in
a pull request must be signed off.** If you forget, amend the most recent
commit with `git commit --amend -s`, or sign off a whole branch against `main`
with `git rebase --signoff main`.

A DCO check runs on every pull request and will flag any commit missing a valid
`Signed-off-by` line, with instructions on how to fix it.

## Development workflow

This is a [uv](https://docs.astral.sh/uv/) project. To get started:

```bash
uv sync                 # install the package + dev tools
uv run pytest           # run the test suite
```

Please make sure the tests pass before opening a pull request, and add tests
for new behavior.
