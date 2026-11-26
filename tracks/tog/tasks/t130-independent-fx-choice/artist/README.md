# Forwardable offline shot brief

Send the artist the single file [brief-zh.html](brief-zh.html) and, if helpful, a neutral starting view. Open it locally in a browser. The artist can describe any relevant shot in their own words or decline. The form has no network dependencies, saved drafts, research links, prescribed choice or numerical cutoff. A download saves the reply on the artist's device. The artist decides whether to share it. A decline exports only its disposition and schema, even if the artist typed a draft first.

Keep the returned JSON outside the repository. In a private directory, record a receipt before opening candidate outcomes:

```text
python seal.py PRIVATE_REPLY.json --seal NEW_RECEIPT.json
python seal.py PRIVATE_REPLY.json --verify NEW_RECEIPT.json
```

The receipt contains the SHA-256 of the exact bytes, byte length, self-reported eligibility class and local-clock UTC sealing time. It excludes the brief, participant name and input path. The command refuses to replace an existing receipt. Store the receipt privately or, with permission, commit it independently before the trial. Its local timestamp alone does not prove chronology, authorship or professional experience. Keep the original bytes when confirming a later interpretation of the brief; record a separately endorsed revision before opening outcomes. The main trial must also account for any already-opened inputs and any coordinator exposure.

An offline Edge fixture check downloaded three temporary replies through the form, preserving Chinese text, spaces and line breaks. The declined export omitted the filled draft. These browser and receipt checks sent zero HTTP requests and exercised the previously-exposed path, refusal to overwrite, duplicate-key rejection and detection of changed bytes. No participant reply or fixture is included.
