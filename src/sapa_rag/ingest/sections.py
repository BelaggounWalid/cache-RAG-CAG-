"""Map every PDF page to its TOC L1 / L2 section."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class SectionMap:
    by_page: dict[int, tuple[str | None, str | None]]

    @classmethod
    def build(cls, toc: list[tuple[int, str, int]], total_pages: int) -> "SectionMap":
        # Sort by page; iterate forward filling L1/L2 until next entry replaces them.
        toc_sorted = sorted(toc, key=lambda x: x[2])
        by_page: dict[int, tuple[str | None, str | None]] = {}
        cur_l1: str | None = None
        cur_l2: str | None = None
        idx = 0
        for page in range(1, total_pages + 1):
            while idx < len(toc_sorted) and toc_sorted[idx][2] <= page:
                lvl, title, _ = toc_sorted[idx]
                title = title.replace("\n", " ").strip()
                if lvl == 1:
                    cur_l1, cur_l2 = title, None
                elif lvl == 2:
                    cur_l2 = title
                idx += 1
            by_page[page] = (cur_l1, cur_l2)
        return cls(by_page=by_page)

    def get(self, page: int) -> tuple[str | None, str | None]:
        return self.by_page.get(page, (None, None))
