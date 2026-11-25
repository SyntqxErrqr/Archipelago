"""
Live memory access for the Windows Steam build of BIT.TRIP RUNNER (RUNNER.exe, 32-bit).

How the integration works:

The game keeps its whole save file in memory as one static struct. Every level has a 28-byte record in it, and the first
byte of a level's record ("cleared") is what the vanilla game uses to decide whether the *next* level is unlocked.
Rather than fight over those bytes with the game, the client allocates its own small table inside the game process
(the "AP table", same 28-byte stride as the save records) and rewrites the displacement of a handful of instructions so
that:

* the level select asks the AP table whether a level is unlocked (written by the client from received items),
* the main menu asks the AP table whether zones 2 and 3 can be entered,
* finishing a level writes the cleared / perfect / bonus flags into the AP table instead of the save,
* the "PERFECT" markers on the level select read the AP table, so they show progress in this seed.

The real save file is never written by the client, so a player's vanilla progress survives a randomizer run untouched.

The game also auto-advances to the next level after finishing one. The client rewrites the game's next-level table so
that it only ever advances into levels that are unlocked.

Only Windows is supported, since this works through ReadProcessMemory/WriteProcessMemory.
"""
from __future__ import annotations

import ctypes
import struct
import sys
from dataclasses import dataclass
from typing import NamedTuple

PROCESS_NAME = "RUNNER.exe"

IMAGE_BASE = 0x400000
"""The address RUNNER.exe asks to be loaded at. The exe has no ASLR, so this is where it always ends up."""

SAVE_ADDRESS = 0x5BAD20
"""Start of the in-memory save file: u32 version, u32 crc32, u32 difficulty, then the level records."""
SAVE_DIFFICULTY_ADDRESS = SAVE_ADDRESS + 8
SAVE_RECORDS_ADDRESS = SAVE_ADDRESS + 12

NEXT_LEVEL_TABLE_ADDRESS = 0x528DD8
"""36 entries of (s32 world, s32 level) used to pick the level that follows the one just finished."""

CURRENT_WORLD_ADDRESS = 0x567D20
"""Index into the world descriptor table: 0-2 are the zones, 3-5 the bonus stages of each zone, 6+ cutscenes."""
WORLD_DESCRIPTOR_TABLE_ADDRESS = 0x537070

RECORD_SIZE = 28
LEVELS_PER_ZONE = 12
ZONES = 3
LEVELS_PER_DIFFICULTY = LEVELS_PER_ZONE * ZONES
DIFFICULTIES = 3
RECORD_COUNT = LEVELS_PER_DIFFICULTY * DIFFICULTIES

# Offsets inside each 28-byte record of the AP table.
K_UNLOCKED = 0
K_CLEARED = 4
K_PERFECT = 5  # Must be K_CLEARED + 1: the level-complete code writes "perfect" relative to the "cleared" pointer.
K_BONUS = 6  # Must be K_CLEARED + 2: the level select reads "bonus" relative to the "cleared" pointer.
K_ZONE_UNLOCKED = 8  # Only meaningful in the first record of zones 2 and 3.

AP_BLOCK_SIZE = 0x1000
AP_HEADER_SIZE = 0x40
AP_MAGIC = b"APBTRUN1"
AP_IDENTITY_OFFSET = 0x08  # 32-byte slot identity (seed name + slot), used to notice a new seed in a running game.
AP_IDENTITY_SIZE = 0x20


class DisplacementPatch(NamedTuple):
    address: int
    """Address of the instruction."""
    original: bytes
    """Exact instruction bytes in vanilla RUNNER.exe. The displacement inside is checked before patching."""
    displacement_offset: int
    """Where the 32-bit displacement sits inside the instruction."""
    table_offset: int
    """What the displacement should become, relative to the start of the AP records."""


def _disp(address: int) -> bytes:
    return struct.pack("<I", address)


# Every instruction below addresses a save record as [index * 28 + displacement] (or [difficulty * 1008 + displacement]
# for the first level of a zone). Swapping the displacement for one inside the AP table keeps the indexing math the game
# already does, so no new code has to be injected. Comments give the vanilla meaning of each read or write.
DISPLACEMENT_PATCHES: tuple[DisplacementPatch, ...] = (
    # Level select: "is this level locked?" Vanilla reads the previous level's cleared flag.
    # In order: first level of zone 2, rest of zone 2, first level of zone 3, then zones 1 and 3.
    DisplacementPatch(0x41382C, b"\x38\x82" + _disp(0x5BAE60), 2, 12 * RECORD_SIZE + K_UNLOCKED),
    DisplacementPatch(0x41384C, b"\x38\x04\x8D" + _disp(0x5BAE60), 3, 12 * RECORD_SIZE + K_UNLOCKED),
    DisplacementPatch(0x413869, b"\x38\x82" + _disp(0x5BAFB0), 2, 24 * RECORD_SIZE + K_UNLOCKED),
    DisplacementPatch(0x413889, b"\x38\x04\x8D" + _disp(0x5BAD10), 3, K_UNLOCKED),
    # Main menu: can zone 2 / zone 3 be highlighted and entered? Vanilla reads the previous zone's boss cleared flag.
    DisplacementPatch(0x413C4A, b"\x80\xBA" + _disp(0x5BAE60) + b"\x00", 2, 12 * RECORD_SIZE + K_ZONE_UNLOCKED),
    DisplacementPatch(0x413C63, b"\x80\xB8" + _disp(0x5BAFB0) + b"\x00", 2, 24 * RECORD_SIZE + K_ZONE_UNLOCKED),
    DisplacementPatch(0x413E59, b"\x80\xBA" + _disp(0x5BAE60) + b"\x00", 2, 12 * RECORD_SIZE + K_ZONE_UNLOCKED),
    DisplacementPatch(0x413E76, b"\x80\xB8" + _disp(0x5BAFB0) + b"\x00", 2, 24 * RECORD_SIZE + K_ZONE_UNLOCKED),
    DisplacementPatch(0x415D26, b"\x80\xBA" + _disp(0x5BAE60) + b"\x00", 2, 12 * RECORD_SIZE + K_ZONE_UNLOCKED),
    DisplacementPatch(0x415D40, b"\x80\xB9" + _disp(0x5BAFB0) + b"\x00", 2, 24 * RECORD_SIZE + K_ZONE_UNLOCKED),
    # Main menu zone "PERFECT" markers (every non-boss level perfected / bonus perfected).
    DisplacementPatch(0x413CDB, b"\x80\x3C\xBD" + _disp(0x5BAD2D) + b"\x00", 3, K_PERFECT),
    DisplacementPatch(0x413D3B, b"\x80\x3C\x9D" + _disp(0x5BAD2E) + b"\x00", 3, K_BONUS),
    # Level select per-level markers. The index here is 1-based, hence the record_size step back.
    DisplacementPatch(0x4141B8, b"\x80\x3C\x95" + _disp(0x5BAD11) + b"\x00", 3, K_PERFECT - RECORD_SIZE),
    DisplacementPatch(0x4141C0, b"\x8D\x04\x95" + _disp(0x5BAD10), 3, K_CLEARED - RECORD_SIZE),
    # Level complete: set "bonus perfect" after a bonus stage, "cleared" (+ "perfect") after a normal level.
    DisplacementPatch(0x418671, b"\xC6\x04\x95" + _disp(0x5BAD2E) + b"\x01", 3, K_BONUS),
    DisplacementPatch(0x41869D, b"\x8D\x04\x95" + _disp(0x5BAD2C), 3, K_CLEARED),
)

# Vanilla never treats 1-1 as locked (it returns early). Turning that branch into an unconditional jump sends 1-1
# through the same table lookup as every other level, so it can be locked too.
FIRST_LEVEL_BRANCH_ADDRESS = 0x413806
FIRST_LEVEL_BRANCH_VANILLA = b"\x75\x03"
FIRST_LEVEL_BRANCH_PATCHED = b"\xEB\x03"


class GameMemoryError(Exception):
    pass


class UnsupportedGameVersion(GameMemoryError):
    pass


@dataclass
class LevelFlags:
    cleared: bool
    perfect: bool
    bonus: bool


def record_index(difficulty: int, level_index: int) -> int:
    """Index of a record inside the save / AP table. level_index is 0-35 (zone * 12 + level)."""
    return difficulty * LEVELS_PER_DIFFICULTY + level_index


if sys.platform == "win32":
    import ctypes.wintypes as wintypes

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")

    _PROCESS_VM_OPERATION = 0x0008
    _PROCESS_VM_READ = 0x0010
    _PROCESS_VM_WRITE = 0x0020
    _PROCESS_QUERY_INFORMATION = 0x0400
    _PROCESS_SUSPEND_RESUME = 0x0800
    _SYNCHRONIZE = 0x00100000
    _TH32CS_SNAPPROCESS = 0x2
    _TH32CS_SNAPMODULE = 0x8
    _TH32CS_SNAPMODULE32 = 0x10
    _MEM_COMMIT = 0x1000
    _MEM_RESERVE = 0x2000
    _MEM_RELEASE = 0x8000
    _MEM_FREE = 0x10000
    _PAGE_READWRITE = 0x04
    _PAGE_EXECUTE_READWRITE = 0x40
    _WAIT_TIMEOUT = 0x102
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class _ProcessEntry32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_char * 260),
        ]

    class _ModuleEntry32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("th32ModuleID", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("GlblcntUsage", wintypes.DWORD),
            ("ProccntUsage", wintypes.DWORD),
            ("modBaseAddr", ctypes.c_void_p),
            ("modBaseSize", wintypes.DWORD),
            ("hModule", wintypes.HMODULE),
            ("szModule", ctypes.c_char * 256),
            ("szExePath", ctypes.c_char * 260),
        ]

    class _MemoryBasicInformation(ctypes.Structure):
        _fields_ = [
            ("BaseAddress", ctypes.c_void_p),
            ("AllocationBase", ctypes.c_void_p),
            ("AllocationProtect", wintypes.DWORD),
            ("PartitionId", wintypes.WORD),
            ("RegionSize", ctypes.c_size_t),
            ("State", wintypes.DWORD),
            ("Protect", wintypes.DWORD),
            ("Type", wintypes.DWORD),
        ]

    _kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry32)]
    _kernel32.Process32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ProcessEntry32)]
    _kernel32.Module32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ModuleEntry32)]
    _kernel32.Module32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(_ModuleEntry32)]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel32.ReadProcessMemory.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    _kernel32.WriteProcessMemory.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    _kernel32.VirtualAllocEx.restype = ctypes.c_void_p
    _kernel32.VirtualAllocEx.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD
    ]
    _kernel32.VirtualFreeEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD]
    _kernel32.VirtualProtectEx.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
    ]
    _kernel32.VirtualQueryEx.restype = ctypes.c_size_t
    _kernel32.VirtualQueryEx.argtypes = [
        wintypes.HANDLE, ctypes.c_void_p, ctypes.POINTER(_MemoryBasicInformation), ctypes.c_size_t
    ]
    _kernel32.FlushInstructionCache.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_size_t]
    _kernel32.WaitForSingleObject.restype = wintypes.DWORD
    _kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _ntdll.NtSuspendProcess.argtypes = [wintypes.HANDLE]
    _ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]


def find_process_id(name: str = PROCESS_NAME) -> int | None:
    if sys.platform != "win32":
        return None
    snapshot = _kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
    if snapshot == _INVALID_HANDLE_VALUE:
        return None
    try:
        entry = _ProcessEntry32()
        entry.dwSize = ctypes.sizeof(_ProcessEntry32)
        found = _kernel32.Process32First(snapshot, ctypes.byref(entry))
        while found:
            if entry.szExeFile.decode(errors="ignore").lower() == name.lower():
                return int(entry.th32ProcessID)
            found = _kernel32.Process32Next(snapshot, ctypes.byref(entry))
    finally:
        _kernel32.CloseHandle(snapshot)
    return None


class RunnerProcess:
    """An open handle to a running RUNNER.exe, with the AP patches applied."""

    def __init__(self, pid: int) -> None:
        if sys.platform != "win32":
            raise GameMemoryError("BIT.TRIP RUNNER memory access is only supported on Windows.")
        self.pid = pid
        access = (_PROCESS_VM_OPERATION | _PROCESS_VM_READ | _PROCESS_VM_WRITE | _PROCESS_QUERY_INFORMATION
                  | _PROCESS_SUSPEND_RESUME | _SYNCHRONIZE)
        self._handle = _kernel32.OpenProcess(access, False, pid)
        if not self._handle:
            raise GameMemoryError(f"Could not open RUNNER.exe (error {ctypes.get_last_error()}).")
        self._base = self._find_module_base()
        self.table_address: int = 0
        """Address of the first AP record (the AP header sits right before it)."""

    @classmethod
    def attach(cls) -> RunnerProcess | None:
        pid = find_process_id()
        if pid is None:
            return None
        return cls(pid)

    # ---- low level -------------------------------------------------------------------------------------------------

    def close(self) -> None:
        if self._handle:
            _kernel32.CloseHandle(self._handle)
            self._handle = None

    def is_alive(self) -> bool:
        if not self._handle:
            return False
        return _kernel32.WaitForSingleObject(self._handle, 0) == _WAIT_TIMEOUT

    def _find_module_base(self) -> int:
        snapshot = _kernel32.CreateToolhelp32Snapshot(_TH32CS_SNAPMODULE | _TH32CS_SNAPMODULE32, self.pid)
        if snapshot == _INVALID_HANDLE_VALUE:
            # The process may still be starting up; the exe has no ASLR, so the preferred base is a safe fallback.
            return IMAGE_BASE
        try:
            entry = _ModuleEntry32()
            entry.dwSize = ctypes.sizeof(_ModuleEntry32)
            found = _kernel32.Module32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.szModule.decode(errors="ignore").lower() == PROCESS_NAME.lower():
                    return int(entry.modBaseAddr or IMAGE_BASE)
                found = _kernel32.Module32Next(snapshot, ctypes.byref(entry))
        finally:
            _kernel32.CloseHandle(snapshot)
        return IMAGE_BASE

    def _rebase(self, address: int) -> int:
        return address - IMAGE_BASE + self._base

    def read(self, address: int, size: int) -> bytes:
        buffer = ctypes.create_string_buffer(size)
        read = ctypes.c_size_t()
        if not _kernel32.ReadProcessMemory(self._handle, ctypes.c_void_p(address), buffer, size, ctypes.byref(read)) \
                or read.value != size:
            raise GameMemoryError(f"Reading {size} bytes at {address:#x} failed (error {ctypes.get_last_error()}).")
        return buffer.raw

    def write(self, address: int, data: bytes) -> None:
        written = ctypes.c_size_t()
        if not _kernel32.WriteProcessMemory(self._handle, ctypes.c_void_p(address), data, len(data),
                                            ctypes.byref(written)) or written.value != len(data):
            raise GameMemoryError(f"Writing {len(data)} bytes at {address:#x} failed "
                                  f"(error {ctypes.get_last_error()}).")

    def read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.read(address, 4))[0]

    def _write_code(self, address: int, data: bytes) -> None:
        old_protect = wintypes.DWORD()
        if not _kernel32.VirtualProtectEx(self._handle, ctypes.c_void_p(address), len(data), _PAGE_EXECUTE_READWRITE,
                                          ctypes.byref(old_protect)):
            raise GameMemoryError(f"Could not unprotect code at {address:#x} (error {ctypes.get_last_error()}).")
        try:
            self.write(address, data)
        finally:
            _kernel32.VirtualProtectEx(self._handle, ctypes.c_void_p(address), len(data), old_protect.value,
                                       ctypes.byref(wintypes.DWORD()))
            _kernel32.FlushInstructionCache(self._handle, ctypes.c_void_p(address), len(data))

    def _allocate_low(self, size: int) -> int:
        """Allocate memory the 32-bit game can address (below 2 GiB)."""
        address = _kernel32.VirtualAllocEx(self._handle, None, size, _MEM_COMMIT | _MEM_RESERVE, _PAGE_READWRITE)
        if address and address + size <= 0x7FFF0000:
            return int(address)
        if address:
            _kernel32.VirtualFreeEx(self._handle, ctypes.c_void_p(address), 0, _MEM_RELEASE)
        # Walk the address space for a free hole instead.
        info = _MemoryBasicInformation()
        candidate = 0x10000000
        while candidate < 0x7FFF0000:
            if not _kernel32.VirtualQueryEx(self._handle, ctypes.c_void_p(candidate), ctypes.byref(info),
                                            ctypes.sizeof(info)):
                break
            region_start = int(info.BaseAddress or 0)
            region_end = region_start + int(info.RegionSize)
            if info.State == _MEM_FREE:
                aligned = (max(region_start, candidate) + 0xFFFF) & ~0xFFFF
                if aligned + size <= region_end:
                    address = _kernel32.VirtualAllocEx(self._handle, ctypes.c_void_p(aligned), size,
                                                       _MEM_COMMIT | _MEM_RESERVE, _PAGE_READWRITE)
                    if address:
                        return int(address)
            candidate = max(region_end, candidate + 0x10000)
        raise GameMemoryError("Could not allocate memory inside RUNNER.exe.")

    # ---- setup -----------------------------------------------------------------------------------------------------

    def _existing_table(self) -> int | None:
        """
        Check every patch site.

        Returns the address of the AP table if a previous client session already patched this process, else None.
        Raises UnsupportedGameVersion if an instruction looks like neither vanilla nor our patch.
        """
        existing_table: int | None = None
        for patch in DISPLACEMENT_PATCHES:
            address = self._rebase(patch.address)
            current = self.read(address, len(patch.original))
            expected = bytearray(patch.original)
            vanilla_target = struct.unpack_from("<I", patch.original, patch.displacement_offset)[0]
            struct.pack_into("<I", expected, patch.displacement_offset, self._rebase(vanilla_target))
            if current == bytes(expected):
                continue
            # Same instruction with a different displacement: a client already patched this process.
            prefix_ok = current[:patch.displacement_offset] == expected[:patch.displacement_offset]
            suffix_ok = current[patch.displacement_offset + 4:] == expected[patch.displacement_offset + 4:]
            if not (prefix_ok and suffix_ok):
                raise UnsupportedGameVersion(
                    f"Unexpected code at {address:#x}. Only the current Windows Steam build of BIT.TRIP RUNNER "
                    f"is supported."
                )
            displacement = struct.unpack_from("<I", current, patch.displacement_offset)[0]
            table = (displacement - patch.table_offset) & 0xFFFFFFFF
            if existing_table is None:
                existing_table = table
            elif existing_table != table:
                raise GameMemoryError("RUNNER.exe is in a half-patched state. Restart the game and try again.")
        return existing_table

    def code_is_decrypted(self) -> bool:
        """The Steam DRM wrapper decrypts the code shortly after launch. Patching before that would corrupt it."""
        try:
            first = DISPLACEMENT_PATCHES[0]
            return self.read(self._rebase(first.address), 2) == first.original[:2]
        except GameMemoryError:
            return False

    def save_loaded(self) -> bool:
        """The save struct is filled in once the player presses a button on the title screen."""
        try:
            return self.read_u32(self._rebase(SAVE_ADDRESS)) == 1
        except GameMemoryError:
            return False

    def install(self) -> None:
        """Apply the AP patches (or adopt the ones a previous client session already applied)."""
        existing_table = self._existing_table()
        if existing_table is not None:
            header = self.read(existing_table - AP_HEADER_SIZE, len(AP_MAGIC))
            if header != AP_MAGIC:
                raise GameMemoryError("RUNNER.exe was patched by something else. Restart the game and try again.")
            self.table_address = existing_table
            return

        block = self._allocate_low(AP_BLOCK_SIZE)
        table = block + AP_HEADER_SIZE
        self.write(block, AP_MAGIC)

        _ntdll.NtSuspendProcess(self._handle)
        try:
            for patch in DISPLACEMENT_PATCHES:
                address = self._rebase(patch.address) + patch.displacement_offset
                self._write_code(address, struct.pack("<I", (table + patch.table_offset) & 0xFFFFFFFF))
            branch = self._rebase(FIRST_LEVEL_BRANCH_ADDRESS)
            if self.read(branch, 2) == FIRST_LEVEL_BRANCH_VANILLA:
                self._write_code(branch, FIRST_LEVEL_BRANCH_PATCHED)
        finally:
            _ntdll.NtResumeProcess(self._handle)
        self.table_address = table

    # ---- AP table --------------------------------------------------------------------------------------------------

    def read_identity(self) -> bytes:
        return self.read(self.table_address - AP_HEADER_SIZE + AP_IDENTITY_OFFSET, AP_IDENTITY_SIZE)

    def claim_for_slot(self, identity: bytes) -> bool:
        """
        Tie the AP table to one seed + slot. If it belonged to a different one, its progress flags are wiped.

        Returns True if the flags were wiped.
        """
        identity = identity[:AP_IDENTITY_SIZE].ljust(AP_IDENTITY_SIZE, b"\0")
        if self.read_identity() == identity:
            return False
        self.write(self.table_address, bytes(RECORD_COUNT * RECORD_SIZE))
        self.write(self.table_address - AP_HEADER_SIZE + AP_IDENTITY_OFFSET, identity)
        return True

    def read_records(self) -> bytes:
        return self.read(self.table_address, RECORD_COUNT * RECORD_SIZE)

    def read_level_flags(self) -> dict[tuple[int, int], LevelFlags]:
        """Flags for every (difficulty, level_index) pair."""
        data = self.read_records()
        flags: dict[tuple[int, int], LevelFlags] = {}
        for difficulty in range(DIFFICULTIES):
            for level_index in range(LEVELS_PER_DIFFICULTY):
                offset = record_index(difficulty, level_index) * RECORD_SIZE
                flags[difficulty, level_index] = LevelFlags(
                    cleared=bool(data[offset + K_CLEARED]),
                    perfect=bool(data[offset + K_PERFECT]),
                    bonus=bool(data[offset + K_BONUS]),
                )
        return flags

    def write_unlocks(self, unlocked_levels: set[int], difficulties: set[int]) -> None:
        """Write which levels (0-35) can be played, on which difficulties (0-2)."""
        wanted: dict[int, int] = {}
        for difficulty in range(DIFFICULTIES):
            allowed = difficulty in difficulties
            for level_index in range(LEVELS_PER_DIFFICULTY):
                offset = record_index(difficulty, level_index) * RECORD_SIZE + K_UNLOCKED
                wanted[offset] = int(allowed and level_index in unlocked_levels)
            for zone in (1, 2):
                offset = record_index(difficulty, zone * LEVELS_PER_ZONE) * RECORD_SIZE + K_ZONE_UNLOCKED
                zone_levels = range(zone * LEVELS_PER_ZONE, (zone + 1) * LEVELS_PER_ZONE)
                wanted[offset] = int(allowed and any(level in unlocked_levels for level in zone_levels))

        # Write single bytes rather than the whole table: the game may set a cleared flag between our read and our
        # write, and writing back a stale copy would erase it.
        current = self.read_records()
        for offset, value in wanted.items():
            if current[offset] != value:
                self.write(self.table_address + offset, bytes([value]))

    def write_next_levels(self, next_levels: list[tuple[int, int]]) -> None:
        """Rewrite the game's "level that follows this one" table: 36 (world, level) pairs."""
        data = b"".join(struct.pack("<ii", world, level) for world, level in next_levels)
        address = self._rebase(NEXT_LEVEL_TABLE_ADDRESS)
        if self.read(address, len(data)) != data:
            self.write(address, data)

    # ---- game state ------------------------------------------------------------------------------------------------

    def difficulty(self) -> int:
        return self.read_u32(self._rebase(SAVE_DIFFICULTY_ADDRESS))

    def current_level(self) -> tuple[int, int] | None:
        """(world, level) the game is set to play, or None if unknown. World 3-5 are the bonus stages."""
        world = self.read_u32(self._rebase(CURRENT_WORLD_ADDRESS))
        if world > 7:
            return None
        descriptor = self.read_u32(self._rebase(WORLD_DESCRIPTOR_TABLE_ADDRESS) + 4 * world)
        if not descriptor:
            return None
        level = self.read_u32(descriptor + 0x14)
        return world, level
