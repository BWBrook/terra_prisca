# Later response archives: inventory, 9 November 2026

## Mak et al. (2023)

[Dataset](https://doi.org/10.5281/zenodo.8178651),
[record metadata](https://zenodo.org/api/records/8178651), CC BY 4.0.
The single ZIP is **38,309,598,059 bytes**. The record advertises MD5
`849dfee2f006c76dfa17b489fa802c1f`; the full payload has not been downloaded
or checksum-verified.

Two bounded HTTP range requests read **485,677 bytes** to inventory 2,527
entries. There are 1,405 nonempty UM output files across 14 atmospheric
directories, plus 35 empty output files in the clear CH₄ = 0.375% directory.
The nonempty outputs expand to 82.43 GB. There is no ready temperature table
or analysis code in the archive. The [compact summary](archive_inventory/mak_summary.json)
records case/stream sizes; the complete directory remains untracked.

Sample headers identify a surface-temperature field in stream `pb`, on a
90 × 144 latitude–longitude grid, with time-mean metadata. All 281 nonempty
`pb` files total **14,915,512,568 compressed bytes**, expanding to
26,955,229,376 bytes. This identifies a smaller extraction target, but ZIP
deflation prevents simple network seeking directly to each interior field.
No temperature response or global mean has been calculated from these files.

Reproduce the directory inventory without downloading climate payloads:

```bash
uv run python -m terra_prisca.haze_response.inventory_mak2023 local/haze/inventory
```

The script refuses a server that ignores byte ranges, caps individual reads
at 2 MB and checks the published archive identity before reading. Its parser
was replayed against the saved directory bytes and reproduced all entries.
Only the compact numerical summary is committed. No remote host or large
download was needed for this step. Later payload extraction belongs on the
project's data/compute host and needs correct temporal bounds, empty-file
handling, grid-area weighting and a comparison with the paper's averaging.

## Eager-Nash et al. (2023)

[Dataset DOI](https://doi.org/10.24378/exe.4347),
[DataCite metadata](https://api.datacite.org/dois/10.24378/exe.4347),
[repository handle](https://ore.exeter.ac.uk/handle/10871/131840).
DataCite confirms CC BY 4.0. The landing page and ordinary public metadata
endpoint returned an empty HTTP 202 response from the site's web-application
challenge. Exact files, sizes and formats remain **unverified**. We made no
attempt to bypass that response and did not substitute a guessed inventory.

This source remains a candidate for extending the haze-free methane domain;
it is not yet a downloaded or accepted baseline.
