from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:  # pragma: no cover - tkinter should exist on Windows Python
    tk = None
    filedialog = messagebox = ttk = None


APP_TITLE = "파일명구조대"
DEFAULT_FOLDER = Path.home() / "Downloads"

WM_DROPFILES = 0x0233
WM_NCDESTROY = 0x0082
GWL_WNDPROC = -4
DROPFILES_COUNT = 0xFFFFFFFF

LRESULT = ctypes.c_ssize_t
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    ctypes.c_void_p,
    ctypes.c_uint,
    ctypes.c_size_t,
    ctypes.c_ssize_t,
)


@dataclass(slots=True)
class RenameItem:
    source: Path
    target_name: str
    kind: str
    depth: int
    conflict: str | None = None

    @property
    def target(self) -> Path:
        return self.source.with_name(self.target_name)


@dataclass(slots=True)
class RenamePlan:
    scope_label: str
    items: list[RenameItem]

    @property
    def candidates(self) -> list[RenameItem]:
        return [item for item in self.items if not item.conflict]

    @property
    def conflicts(self) -> list[RenameItem]:
        return [item for item in self.items if item.conflict]


def normalize_name(name: str) -> str:
    return unicodedata.normalize("NFC", name)


def path_depth(path: Path) -> int:
    return len(path.parts)


def target_key(name: str) -> str:
    return os.path.normcase(name)


def unique_existing_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for raw_path in paths:
        path = raw_path.expanduser()
        try:
            key = os.path.normcase(str(path.resolve(strict=False)))
        except OSError:
            key = os.path.normcase(str(path))
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            result.append(path)
    return result


def scan_paths(root: Path, recursive: bool, include_dirs: bool) -> Iterable[Path]:
    if recursive:
        for current_root, dirs, files in os.walk(root, topdown=False):
            current = Path(current_root)
            for filename in files:
                yield current / filename
            if include_dirs:
                for dirname in dirs:
                    yield current / dirname
        return

    for child in root.iterdir():
        if child.is_file():
            yield child
        elif include_dirs and child.is_dir():
            yield child


def collect_target_paths(
    targets: Sequence[Path],
    recursive: bool = True,
    include_dirs: bool = True,
) -> list[Path]:
    collected: list[Path] = []

    for target in unique_existing_paths(targets):
        if target.is_file():
            collected.append(target)
            continue

        if target.is_dir():
            if include_dirs:
                collected.append(target)
            collected.extend(scan_paths(target, recursive=recursive, include_dirs=include_dirs))

    return unique_existing_paths(collected)


def describe_targets(targets: Sequence[Path]) -> str:
    valid_targets = unique_existing_paths(targets)
    if not valid_targets:
        return "선택 항목"
    if len(valid_targets) == 1:
        return str(valid_targets[0])

    try:
        common_root = Path(os.path.commonpath([str(path) for path in valid_targets]))
        return f"드롭한 {len(valid_targets)}개 항목 (공통 경로: {common_root})"
    except ValueError:
        return f"드롭한 {len(valid_targets)}개 항목"


def build_plan_from_paths(paths: Iterable[Path], scope_label: str) -> RenamePlan:
    items: list[RenameItem] = []
    by_parent: dict[Path, list[RenameItem]] = defaultdict(list)

    for path in unique_existing_paths(paths):
        target_name = normalize_name(path.name)
        if target_name == path.name:
            continue

        item = RenameItem(
            source=path,
            target_name=target_name,
            kind="folder" if path.is_dir() else "file",
            depth=path_depth(path),
        )
        items.append(item)
        by_parent[path.parent].append(item)

    for siblings in by_parent.values():
        counts = Counter(target_key(item.target_name) for item in siblings)
        for item in siblings:
            if counts[target_key(item.target_name)] > 1:
                item.conflict = "같은 폴더 안에서 정규화 후 이름이 서로 겹칩니다."

        for item in siblings:
            if item.conflict:
                continue
            if item.target.exists():
                item.conflict = "정규화된 목표 이름의 파일 또는 폴더가 이미 존재합니다."

    items.sort(key=lambda item: (item.depth, item.kind == "folder"), reverse=True)
    return RenamePlan(scope_label=scope_label, items=items)


def build_plan_for_folder(root: Path, recursive: bool = True, include_dirs: bool = True) -> RenamePlan:
    return build_plan_from_paths(
        scan_paths(root, recursive=recursive, include_dirs=include_dirs),
        scope_label=str(root),
    )


def build_plan_for_targets(
    targets: Sequence[Path],
    recursive: bool = True,
    include_dirs: bool = True,
) -> RenamePlan:
    return build_plan_from_paths(
        collect_target_paths(targets, recursive=recursive, include_dirs=include_dirs),
        scope_label=describe_targets(targets),
    )


def apply_plan(plan: RenamePlan) -> tuple[list[dict[str, str]], list[dict[str, str]], Path | None]:
    renamed: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    for item in plan.items:
        if item.conflict:
            skipped.append(
                {
                    "source": str(item.source),
                    "target": str(item.target),
                    "reason": item.conflict,
                }
            )
            continue

        source = item.source
        target = item.target

        if not source.exists():
            skipped.append(
                {
                    "source": str(source),
                    "target": str(target),
                    "reason": "원본 경로가 더 이상 존재하지 않습니다.",
                }
            )
            continue

        if target.exists():
            skipped.append(
                {
                    "source": str(source),
                    "target": str(target),
                    "reason": "이름 변경 시점에 목표 경로가 이미 존재합니다.",
                }
            )
            continue

        source.rename(target)
        renamed.append({"source": str(source), "target": str(target), "kind": item.kind})

    log_path = None
    if renamed or skipped:
        log_path = write_log(plan.scope_label, renamed, skipped)

    return renamed, skipped, log_path


def write_log(scope_label: str, renamed: list[dict[str, str]], skipped: list[dict[str, str]]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = Path(__file__).with_name(f"hangul_filename_fixer_log_{timestamp}.json")
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "scope": scope_label,
        "renamed": renamed,
        "skipped": skipped,
    }
    log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return log_path


def format_line(item: RenameItem) -> str:
    status = "CONFLICT" if item.conflict else "READY"
    return f"[{status}] {item.kind.upper()} | {item.source.name} -> {item.target_name}"


def build_plan_for_cli_inputs(
    inputs: Sequence[Path],
    recursive: bool,
    include_dirs: bool,
) -> RenamePlan:
    if len(inputs) == 1 and inputs[0].exists() and inputs[0].is_dir():
        return build_plan_for_folder(inputs[0], recursive=recursive, include_dirs=include_dirs)
    return build_plan_for_targets(inputs, recursive=recursive, include_dirs=include_dirs)


def run_cli(inputs: Sequence[Path], recursive: bool, include_dirs: bool, apply_changes: bool) -> int:
    plan = build_plan_for_cli_inputs(inputs, recursive=recursive, include_dirs=include_dirs)
    print(f"대상: {plan.scope_label}")
    print(f"변경 후보: {len(plan.items)}")
    print(f"즉시 변경 가능: {len(plan.candidates)}")
    print(f"충돌/건너뜀: {len(plan.conflicts)}")
    print()

    for item in plan.items:
        print(format_line(item))
        if item.conflict:
            print(f"  reason: {item.conflict}")

    if not apply_changes:
        return 0

    print()
    renamed, skipped, log_path = apply_plan(plan)
    print(f"변경 완료: {len(renamed)}")
    print(f"건너뜀: {len(skipped)}")
    if log_path is not None:
        print(f"로그 저장: {log_path}")
    return 0


class DropTargetHook:
    def __init__(self, root: tk.Tk, on_drop: callable) -> None:
        self.root = root
        self.on_drop = on_drop
        self.user32 = ctypes.windll.user32
        self.shell32 = ctypes.windll.shell32
        self.old_wndproc = None
        self.new_wndproc = WNDPROC(self._wndproc)

    def install(self) -> bool:
        if os.name != "nt":
            return False

        self.root.update_idletasks()
        hwnd = self.root.winfo_id()

        self.user32.SetWindowLongPtrW.restype = ctypes.c_void_p
        self.user32.SetWindowLongPtrW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_void_p,
        ]
        self.user32.CallWindowProcW.restype = LRESULT
        self.user32.CallWindowProcW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        ]
        self.user32.DefWindowProcW.restype = LRESULT
        self.user32.DefWindowProcW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        ]
        self.shell32.DragQueryFileW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_wchar_p,
            ctypes.c_uint,
        ]
        self.shell32.DragQueryFileW.restype = ctypes.c_uint
        self.shell32.DragAcceptFiles.argtypes = [ctypes.c_void_p, ctypes.c_bool]
        self.shell32.DragFinish.argtypes = [ctypes.c_void_p]

        self.old_wndproc = self.user32.SetWindowLongPtrW(
            hwnd,
            GWL_WNDPROC,
            ctypes.cast(self.new_wndproc, ctypes.c_void_p),
        )
        self.shell32.DragAcceptFiles(hwnd, True)
        return True

    def uninstall(self) -> None:
        if self.old_wndproc is None:
            return
        try:
            hwnd = self.root.winfo_id()
        except tk.TclError:
            return
        self.user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, self.old_wndproc)
        self.old_wndproc = None

    def _call_old(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if self.old_wndproc:
            return self.user32.CallWindowProcW(self.old_wndproc, hwnd, msg, wparam, lparam)
        return self.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _read_drop_paths(self, hdrop: int) -> list[str]:
        count = self.shell32.DragQueryFileW(hdrop, DROPFILES_COUNT, None, 0)
        results: list[str] = []
        for index in range(count):
            length = self.shell32.DragQueryFileW(hdrop, index, None, 0)
            buffer = ctypes.create_unicode_buffer(length + 1)
            self.shell32.DragQueryFileW(hdrop, index, buffer, length + 1)
            results.append(buffer.value)
        return results

    def _wndproc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_DROPFILES:
            paths = self._read_drop_paths(wparam)
            self.shell32.DragFinish(wparam)
            self.root.after(0, lambda: self.on_drop(paths))
            return 0

        if msg == WM_NCDESTROY:
            result = self._call_old(hwnd, msg, wparam, lparam)
            self.uninstall()
            return result

        return self._call_old(hwnd, msg, wparam, lparam)


class FixerApp:
    def __init__(self, root: tk.Tk, initial_inputs: Sequence[Path] | None = None) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1220x780")
        self.root.minsize(1020, 680)

        self.folder_var = tk.StringVar(value=str(DEFAULT_FOLDER))
        self.recursive_var = tk.BooleanVar(value=True)
        self.include_dirs_var = tk.BooleanVar(value=True)
        self.summary_var = tk.StringVar(value="폴더를 스캔하거나 파일 여러 개를 창에 드래그해서 놓아주세요.")
        self.status_var = tk.StringVar(
            value="원인: 한글 파일명이 분해형 유니코드(NFD)로 저장되어 Windows 일부 앱에서 자모가 깨져 보입니다."
        )
        self.drop_var = tk.StringVar(
            value="여기로 파일/폴더 여러 개를 드래그해서 놓으면 그 항목만 따로 스캔합니다."
        )
        self.mode_var = tk.StringVar(value="현재 모드: 폴더 스캔")

        self.plan: RenamePlan | None = None
        self.selected_targets: list[Path] = []
        self.drop_hook: DropTargetHook | None = None

        self._build_ui()
        self._install_drop_support()

        if initial_inputs:
            self.load_targets(initial_inputs, source="인수로 전달된 항목")

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        header = ttk.Frame(self.root, padding=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ttk.Label(header, text=APP_TITLE, font=("Malgun Gothic", 16, "bold")).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(
            header,
            text="분해된 한글 파일명을 찾아 정상 한글(NFC) 이름으로 바꿔주는 도구입니다.",
        ).grid(row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

        ttk.Label(header, text="대상 폴더").grid(row=2, column=0, sticky="w", pady=(12, 0))
        folder_entry = ttk.Entry(header, textvariable=self.folder_var)
        folder_entry.grid(row=2, column=1, sticky="ew", padx=(8, 8), pady=(12, 0))
        ttk.Button(header, text="폴더 선택", command=self.choose_folder).grid(
            row=2,
            column=2,
            sticky="ew",
            pady=(12, 0),
        )
        ttk.Button(header, text="폴더 열기", command=self.open_folder).grid(
            row=2,
            column=3,
            sticky="ew",
            padx=(8, 0),
            pady=(12, 0),
        )

        options = ttk.Frame(header)
        options.grid(row=3, column=0, columnspan=4, sticky="w", pady=(12, 0))
        ttk.Checkbutton(options, text="하위 폴더까지 검색", variable=self.recursive_var).grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Checkbutton(options, text="폴더 이름도 변경", variable=self.include_dirs_var).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(18, 0),
        )
        ttk.Button(options, text="폴더 스캔", command=self.scan_folder).grid(
            row=0,
            column=2,
            padx=(18, 0),
        )
        ttk.Button(options, text="이름 변경 실행", command=self.apply_changes).grid(
            row=0,
            column=3,
            padx=(8, 0),
        )
        ttk.Button(options, text="드롭 목록 지우기", command=self.clear_selection_mode).grid(
            row=0,
            column=4,
            padx=(8, 0),
        )

        drop_frame = ttk.LabelFrame(header, text="드래그 앤 드롭", padding=10)
        drop_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(12, 0))
        drop_frame.columnconfigure(0, weight=1)

        self.drop_label = tk.Label(
            drop_frame,
            textvariable=self.drop_var,
            anchor="w",
            justify="left",
            relief="groove",
            borderwidth=1,
            padx=12,
            pady=12,
            bg="#f7f9fc",
        )
        self.drop_label.grid(row=0, column=0, sticky="ew")

        ttk.Label(header, textvariable=self.mode_var).grid(
            row=5,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(10, 0),
        )
        ttk.Label(header, textvariable=self.summary_var).grid(
            row=6,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(4, 0),
        )
        ttk.Label(header, textvariable=self.status_var, foreground="#3a4d6b").grid(
            row=7,
            column=0,
            columnspan=4,
            sticky="w",
            pady=(4, 0),
        )

        table_frame = ttk.Frame(self.root, padding=(12, 12, 12, 0))
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("status", "kind", "current", "target", "parent")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        self.tree.heading("status", text="상태")
        self.tree.heading("kind", text="유형")
        self.tree.heading("current", text="현재 이름")
        self.tree.heading("target", text="변경될 이름")
        self.tree.heading("parent", text="상위 폴더")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("kind", width=80, anchor="center")
        self.tree.column("current", width=320)
        self.tree.column("target", width=320)
        self.tree.column("parent", width=360)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        note_frame = ttk.LabelFrame(self.root, text="안내", padding=12)
        note_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=12)
        note_frame.columnconfigure(0, weight=1)

        self.note_text = tk.Text(note_frame, height=7, wrap="word")
        self.note_text.grid(row=0, column=0, sticky="ew")
        self.note_text.insert(
            "1.0",
            "대표 원인: macOS/Linux에서 생성하거나 압축 해제한 파일, 또는 클라우드/메신저를 거치며 분해형(NFD) 이름이 유지된 경우입니다.\n"
            "사용 방법 1: 폴더를 선택하고 '폴더 스캔'을 누릅니다.\n"
            "사용 방법 2: 파일 여러 개나 폴더를 창 안으로 드래그해서 놓으면 그 항목만 따로 스캔합니다.\n"
            "드래그한 폴더는 현재 옵션에 따라 하위 폴더와 폴더 이름까지 함께 처리합니다.\n"
            "이름 변경을 실행할 때마다 이 스크립트 옆에 JSON 로그 파일이 저장됩니다.",
        )
        self.note_text.configure(state="disabled")

    def _install_drop_support(self) -> None:
        if os.name != "nt":
            self.status_var.set("현재 운영체제에서는 드래그앤드롭 지원이 비활성화됩니다.")
            return

        self.drop_hook = DropTargetHook(self.root, self.handle_drop)
        try:
            enabled = self.drop_hook.install()
        except Exception as exc:  # pragma: no cover - Windows GUI integration
            self.drop_hook = None
            self.status_var.set(f"드래그앤드롭 초기화에 실패했습니다: {exc}")
            return

        if enabled:
            self.status_var.set(
                "원인: 한글 파일명이 분해형 유니코드(NFD)로 저장되어 Windows 일부 앱에서 자모가 깨져 보입니다. "
                "창으로 파일 여러 개를 바로 드래그해서 놓을 수도 있습니다."
            )

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.folder_var.get() or str(DEFAULT_FOLDER))
        if selected:
            self.folder_var.set(selected)
            self.scan_folder()

    def open_folder(self) -> None:
        folder = Path(self.folder_var.get()).expanduser()
        if not folder.exists():
            messagebox.showerror(APP_TITLE, "선택한 폴더가 존재하지 않습니다.")
            return
        os.startfile(str(folder))

    def clear_selection_mode(self) -> None:
        self.selected_targets = []
        self.mode_var.set("현재 모드: 폴더 스캔")
        self.drop_var.set("여기로 파일/폴더 여러 개를 드래그해서 놓으면 그 항목만 따로 스캔합니다.")
        self.summary_var.set("드롭 목록을 지웠습니다. 다시 폴더를 스캔하거나 파일을 드래그해 주세요.")
        self.status_var.set("기본 모드로 돌아왔습니다. 폴더 스캔 또는 드래그앤드롭을 사용할 수 있습니다.")
        self.plan = None
        self.populate_tree(None)

    def scan_folder(self) -> None:
        folder = Path(self.folder_var.get()).expanduser()
        if not folder.exists() or not folder.is_dir():
            messagebox.showerror(APP_TITLE, "올바른 폴더를 선택해주세요.")
            return

        self.selected_targets = []
        self.mode_var.set("현재 모드: 폴더 스캔")
        self.drop_var.set("여기로 파일/폴더 여러 개를 드래그해서 놓으면 그 항목만 따로 스캔합니다.")

        self.plan = build_plan_for_folder(
            folder,
            recursive=self.recursive_var.get(),
            include_dirs=self.include_dirs_var.get(),
        )
        self.populate_tree(self.plan)
        if self.plan.items:
            self.status_var.set("폴더 스캔 결과를 확인한 뒤 '이름 변경 실행'을 눌러주세요.")
        else:
            self.status_var.set("선택한 폴더에서는 분해형 유니코드 파일명이 발견되지 않았습니다.")

    def load_targets(self, raw_targets: Sequence[Path | str], source: str = "드래그앤드롭") -> None:
        targets = unique_existing_paths(Path(value) for value in raw_targets)
        if not targets:
            self.summary_var.set("유효한 파일이나 폴더를 찾지 못했습니다.")
            self.status_var.set(f"{source}로 들어온 경로 중 현재 존재하는 항목이 없습니다.")
            self.plan = None
            self.populate_tree(None)
            return

        self.selected_targets = list(targets)
        self.mode_var.set(f"현재 모드: 드롭한 항목 {len(targets)}개")
        self.drop_var.set(
            "\n".join(
                [
                    f"{source}로 들어온 항목 {len(targets)}개를 불러왔습니다.",
                    "현재는 폴더 전체가 아니라 이 항목들만 스캔한 상태입니다.",
                ]
            )
        )

        self.plan = build_plan_for_targets(
            self.selected_targets,
            recursive=self.recursive_var.get(),
            include_dirs=self.include_dirs_var.get(),
        )
        self.populate_tree(self.plan)
        if self.plan.items:
            self.status_var.set("드롭한 항목만 따로 스캔했습니다. 목록을 확인한 뒤 '이름 변경 실행'을 눌러주세요.")
        else:
            self.status_var.set("드롭한 항목들에서는 분해형 유니코드 파일명이 발견되지 않았습니다.")

    def handle_drop(self, dropped_paths: Sequence[str]) -> None:
        self.load_targets(dropped_paths, source="드래그앤드롭")

    def populate_tree(self, plan: RenamePlan | None) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        if plan is None:
            self.tree.tag_configure("conflict", background="#fde9e7")
            self.tree.tag_configure("ready", background="#eef8ef")
            return

        for item in plan.items:
            status = "충돌" if item.conflict else "준비"
            kind_label = "폴더" if item.kind == "folder" else "파일"
            self.tree.insert(
                "",
                "end",
                values=(
                    status,
                    kind_label,
                    item.source.name,
                    item.target_name,
                    str(item.source.parent),
                ),
                tags=("conflict",) if item.conflict else ("ready",),
            )

        self.tree.tag_configure("conflict", background="#fde9e7")
        self.tree.tag_configure("ready", background="#eef8ef")
        self.summary_var.set(
            f"변경 대상 {len(plan.items)}개 발견. 바로 변경 가능 {len(plan.candidates)}개 / 충돌 {len(plan.conflicts)}개"
        )

    def current_plan(self) -> RenamePlan | None:
        if self.selected_targets:
            self.plan = build_plan_for_targets(
                self.selected_targets,
                recursive=self.recursive_var.get(),
                include_dirs=self.include_dirs_var.get(),
            )
            return self.plan

        folder = Path(self.folder_var.get()).expanduser()
        if folder.exists() and folder.is_dir():
            self.plan = build_plan_for_folder(
                folder,
                recursive=self.recursive_var.get(),
                include_dirs=self.include_dirs_var.get(),
            )
            return self.plan
        return None

    def apply_changes(self) -> None:
        plan = self.current_plan()
        if plan is None:
            messagebox.showerror(APP_TITLE, "먼저 스캔할 폴더를 선택하거나 파일을 드래그해서 놓아주세요.")
            return

        self.populate_tree(plan)

        if not plan.items:
            messagebox.showinfo(APP_TITLE, "현재 선택에서는 변경할 이름이 없습니다.")
            return

        ready_count = len(plan.candidates)
        conflict_count = len(plan.conflicts)
        confirmed = messagebox.askyesno(
            APP_TITLE,
            f"{ready_count}개 항목의 이름을 변경할까요?\n\n"
            f"충돌로 건너뛸 항목: {conflict_count}개\n"
            "실행 로그(JSON)는 스크립트 옆에 저장됩니다.",
        )
        if not confirmed:
            return

        renamed, skipped, log_path = apply_plan(plan)
        log_text = f"\n로그 파일: {log_path}" if log_path is not None else ""
        messagebox.showinfo(
            APP_TITLE,
            f"변경 완료: {len(renamed)}개\n건너뜀: {len(skipped)}개{log_text}",
        )

        if self.selected_targets:
            updated_targets: list[Path] = []
            for path in self.selected_targets:
                target = path.with_name(normalize_name(path.name))
                updated_targets.append(target if target.exists() else path)
            self.selected_targets = unique_existing_paths(updated_targets)
            self.load_targets(self.selected_targets, source="이름 변경 후 갱신")
            return

        self.scan_folder()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("paths", nargs="*", help="스캔할 폴더 또는 파일/폴더 목록")
    parser.add_argument("--scan", action="store_true", help="CLI 모드로 스캔만 수행")
    parser.add_argument("--apply", action="store_true", help="CLI 모드로 스캔 후 이름 변경 수행")
    parser.add_argument("--no-recursive", action="store_true", help="선택한 폴더만 검색")
    parser.add_argument("--files-only", action="store_true", help="폴더 이름은 변경하지 않음")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    inputs = [Path(value).expanduser() for value in args.paths]
    recursive = not args.no_recursive
    include_dirs = not args.files_only

    if args.scan or args.apply:
        if not inputs:
            print("CLI 모드에서는 경로를 하나 이상 넣어주세요.", file=sys.stderr)
            return 2
        return run_cli(inputs, recursive=recursive, include_dirs=include_dirs, apply_changes=args.apply)

    if tk is None:
        print("이 Python 환경에서는 tkinter를 사용할 수 없습니다.", file=sys.stderr)
        return 1

    root = tk.Tk()
    app = FixerApp(root, initial_inputs=inputs if inputs else None)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
