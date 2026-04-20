"""
MCP2515 CAN Controller Driver for Raspberry Pi (SPI via spidev)

Ported from the Flipper Zero C implementation:
  - libraries/mcp_can_2515.c/.h
  - libraries/Spi_lib.c/.h

Author: dashuai
License: MIT
"""

import time
import spidev


# ---------------------------------------------------------------------------
#  Constants & Register Map  (from mcp_can_2515.h)
# ---------------------------------------------------------------------------

# Frame flags
CAN_IS_EXTENDED       = 0x80000000
CAN_IS_REMOTE_REQUEST = 0x40000000
CAN_EXTENDED_ID       = 0x1FFFFFFF
MAX_LEN               = 8

# CANCTRL bits
CANCTRL_REQOP  = 0xE0
CANCTRL_ABAT   = 0x10
CANCTRL_OSM    = 0x08
CANCTRL_CLKEN  = 0x04
CANCTRL_CLKPRE = 0x03

# CANSTAT bits
CANSTAT_OPM  = 0xE0
CANSTAT_ICOD = 0x0E

# SPI Instructions
INSTRUCTION_WRITE       = 0x02
INSTRUCTION_READ        = 0x03
INSTRUCTION_BITMOD      = 0x05
INSTRUCTION_LOAD_TX0    = 0x40
INSTRUCTION_LOAD_TX1    = 0x42
INSTRUCTION_LOAD_TX2    = 0x44
INSTRUCTION_RTS_TX0     = 0x81
INSTRUCTION_RTS_TX1     = 0x82
INSTRUCTION_RTS_TX2     = 0x84
INSTRUCTION_RTS_ALL     = 0x87
INSTRUCTION_READ_RX0    = 0x90
INSTRUCTION_READ_RX1    = 0x94
INSTRUCTION_READ_STATUS = 0xA0
INSTRUCTION_RX_STATUS   = 0xB0
INSTRUCTION_RESET       = 0xC0

# Registers
MCP_RXF0SIDH = 0x00
MCP_RXF0SIDL = 0x01
MCP_RXF0EID8 = 0x02
MCP_RXF0EID0 = 0x03
MCP_RXF1SIDH = 0x04
MCP_RXF1SIDL = 0x05
MCP_RXF1EID8 = 0x06
MCP_RXF1EID0 = 0x07
MCP_RXF2SIDH = 0x08
MCP_RXF2SIDL = 0x09
MCP_RXF3SIDH = 0x10
MCP_RXF3SIDL = 0x11
MCP_RXF4SIDH = 0x14
MCP_RXF4SIDL = 0x15
MCP_RXF5SIDH = 0x18
MCP_RXF5SIDL = 0x19
MCP_BFPCTRL   = 0x0C
MCP_TXRTSCTRL = 0x0D
MCP_CANSTAT   = 0x0E
MCP_CANCTRL   = 0x0F
MCP_TEC       = 0x1C
MCP_REC       = 0x1D
MCP_RXM0SIDH  = 0x20
MCP_RXM0SIDL  = 0x21
MCP_RXM1SIDH  = 0x24
MCP_RXM1SIDL  = 0x25
MCP_CNF3      = 0x28
MCP_CNF2      = 0x29
MCP_CNF1      = 0x2A
MCP_CANINTE   = 0x2B
MCP_CANINTF   = 0x2C
MCP_EFLG      = 0x2D
MCP_TXB0CTRL  = 0x30
MCP_TXB0SIDH  = 0x31
MCP_TXB0SIDL  = 0x32
MCP_TXB0EID8  = 0x33
MCP_TXB0EID0  = 0x34
MCP_TXB0DLC   = 0x35
MCP_TXB0DATA  = 0x36
MCP_TXB1CTRL  = 0x40
MCP_TXB1SIDH  = 0x41
MCP_TXB1DLC   = 0x45
MCP_TXB1DATA  = 0x46
MCP_TXB2CTRL  = 0x50
MCP_TXB2SIDH  = 0x51
MCP_TXB2DLC   = 0x55
MCP_TXB2DATA  = 0x56
MCP_RXB0CTRL  = 0x60
MCP_RXB0SIDH  = 0x61
MCP_RXB0SIDL  = 0x62
MCP_RXB0EID8  = 0x63
MCP_RXB0EID0  = 0x64
MCP_RXB0DLC   = 0x65
MCP_RXB0DATA  = 0x66
MCP_RXB1CTRL  = 0x70
MCP_RXB1SIDH  = 0x71
MCP_RXB1DLC   = 0x75
MCP_RXB1DATA  = 0x76

# TXBnCTRL / status bits
MCP_TXB_EXIDE_M = 0x08
MCP_DLC_MASK    = 0x0F
MCP_RTR_MASK    = 0x40
MCP_RXB_RX_ANY  = 0x60
MCP_RXB_BUKT_MASK = 0x04

MCP_TXB_TXREQ_M = 0x08

MCP_STAT_TXIF_MASK      = 0xA8
MCP_STAT_TX0IF          = 0x08
MCP_STAT_TX1IF          = 0x20
MCP_STAT_TX2IF          = 0x80
MCP_STAT_TX_PENDING_MASK = 0x54
MCP_STAT_TX0_PENDING    = 0x04
MCP_STAT_TX1_PENDING    = 0x10
MCP_STAT_TX2_PENDING    = 0x40
MCP_STAT_RXIF_MASK      = 0x03
MCP_STAT_RX0IF          = 0x01
MCP_STAT_RX1IF          = 0x02

# CANINTF bits
MCP_RX0IF = 0x01
MCP_RX1IF = 0x02
MCP_TX0IF = 0x04
MCP_TX1IF = 0x08
MCP_TX2IF = 0x10
MCP_ERRIF = 0x20
MCP_WAKIF = 0x40
MCP_MERRF = 0x80

# Error flag bits
MCP_EFLG_RX1OVR    = 0x80
MCP_EFLG_RX0OVR    = 0x40
MCP_EFLG_TXBO      = 0x20
MCP_EFLG_TXEP      = 0x10
MCP_EFLG_RXEP      = 0x08
MCP_EFLG_TXWAR     = 0x04
MCP_EFLG_RXWAR     = 0x02
MCP_EFLG_EWARN     = 0x01
MCP_EFLG_ERRORMASK = 0xF8

MCP_BxBFS_MASK  = 0x30
MCP_BxBFE_MASK  = 0x0C
MCP_BxBFM_MASK  = 0x03
MCP_BxRTS_MASK  = 0x38
MCP_BxRTSM_MASK = 0x07

# ID field offsets within a 4-byte register block
_SIDH = 0
_SIDL = 1
_EID8 = 2
_EID0 = 3


# ---------------------------------------------------------------------------
#  Enums
# ---------------------------------------------------------------------------

class Mode:
    NORMAL     = 0x00
    SLEEP      = 0x20
    LOOPBACK   = 0x40
    LISTENONLY = 0x60
    CONFIG     = 0x80


class BitRate:
    CAN_125KBPS  = 0
    CAN_250KBPS  = 1
    CAN_500KBPS  = 2
    CAN_1000KBPS = 3


class Clock:
    MHZ_8  = 0
    MHZ_16 = 1
    MHZ_20 = 2


class Error:
    OK              = 0
    FAIL            = 1
    ALLTXBUSY       = 2
    FAILINIT        = 3
    FAILTX          = 4
    NOMSG           = 5
    GET_TXB_TIMEOUT = 6
    SEND_MSG_TIMEOUT = 7
    WRONG_BITRATE   = 8


# ---------------------------------------------------------------------------
#  Bit-rate timing table  (CNF1, CNF2, CNF3)
# ---------------------------------------------------------------------------

_BITRATE_TABLE = {
    # (clock, bitrate): (cfg1, cfg2, cfg3)
    (Clock.MHZ_8,  BitRate.CAN_125KBPS):  (0x01, 0xB1, 0x85),
    (Clock.MHZ_8,  BitRate.CAN_250KBPS):  (0x80, 0xE5, 0x83),
    (Clock.MHZ_8,  BitRate.CAN_500KBPS):  (0x00, 0xD1, 0x81),
    (Clock.MHZ_8,  BitRate.CAN_1000KBPS): (0x00, 0xC0, 0x80),

    (Clock.MHZ_16, BitRate.CAN_125KBPS):  (0x03, 0xF0, 0x86),
    (Clock.MHZ_16, BitRate.CAN_250KBPS):  (0x41, 0xF1, 0x85),
    (Clock.MHZ_16, BitRate.CAN_500KBPS):  (0x00, 0xF0, 0x86),
    (Clock.MHZ_16, BitRate.CAN_1000KBPS): (0x00, 0xD0, 0x82),

    (Clock.MHZ_20, BitRate.CAN_125KBPS):  (0x03, 0xFA, 0x87),
    (Clock.MHZ_20, BitRate.CAN_250KBPS):  (0x41, 0xFB, 0x86),
    (Clock.MHZ_20, BitRate.CAN_500KBPS):  (0x00, 0xFA, 0x87),
    (Clock.MHZ_20, BitRate.CAN_1000KBPS): (0x00, 0xD9, 0x82),
}


# ---------------------------------------------------------------------------
#  CAN Frame data class
# ---------------------------------------------------------------------------

class CANFrame:
    """Represents a single CAN frame."""

    __slots__ = ("can_id", "ext", "rtr", "dlc", "data")

    def __init__(self, can_id: int = 0, data: bytes = b"", ext: bool = False, rtr: bool = False):
        self.can_id = can_id
        self.ext = ext
        self.rtr = rtr
        self.dlc = len(data)
        self.data = bytearray(data)

    def __repr__(self):
        hex_data = " ".join(f"{b:02X}" for b in self.data[:self.dlc])
        return f"CANFrame(id=0x{self.can_id:03X}, dlc={self.dlc}, data=[{hex_data}])"


# ---------------------------------------------------------------------------
#  MCP2515 Driver
# ---------------------------------------------------------------------------

class MCP2515:
    """
    MCP2515 CAN controller driver using Linux spidev.

    Usage::

        mcp = MCP2515(bus=0, device=0, clock=Clock.MHZ_8, bitrate=BitRate.CAN_500KBPS)
        err = mcp.init(mode=Mode.LOOPBACK)
        if err != Error.OK:
            print("Init failed!")
        ...
        mcp.close()
    """

    def __init__(self, bus: int = 0, device: int = 0,
                 clock: int = Clock.MHZ_8,
                 bitrate: int = BitRate.CAN_500KBPS,
                 spi_speed: int = 8_000_000):
        self.clock = clock
        self.bitrate = bitrate
        self.mode = Mode.NORMAL
        self._spi_speed = spi_speed

        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)
        self._spi.max_speed_hz = spi_speed
        self._spi.mode = 0b00          # CPOL=0, CPHA=0
        self._spi.bits_per_word = 8
        self._spi.no_cs = False

    # ------------------------------------------------------------------
    #  Low-level SPI helpers
    # ------------------------------------------------------------------

    def _read_register(self, addr: int) -> int:
        resp = self._spi.xfer2([INSTRUCTION_READ, addr, 0x00])
        return resp[2]

    def _write_register(self, addr: int, value: int):
        self._spi.xfer2([INSTRUCTION_WRITE, addr, value])

    def _modify_register(self, addr: int, mask: int, value: int):
        self._spi.xfer2([INSTRUCTION_BITMOD, addr, mask, value])

    def _get_status(self) -> int:
        resp = self._spi.xfer2([INSTRUCTION_READ_STATUS, 0x00])
        return resp[1]

    # ------------------------------------------------------------------
    #  Reset
    # ------------------------------------------------------------------

    def reset(self):
        """Send hardware reset to MCP2515."""
        self._spi.xfer2([INSTRUCTION_RESET])
        time.sleep(0.01)  # 10 ms settle

    # ------------------------------------------------------------------
    #  Mode management
    # ------------------------------------------------------------------

    def _get_mode(self) -> int:
        return self._read_register(MCP_CANSTAT) & CANSTAT_OPM

    def set_mode(self, new_mode: int) -> bool:
        """Switch MCP2515 operating mode. Returns True on success."""
        if self._get_mode() == new_mode:
            return True

        # Wake from sleep if needed
        if self._get_mode() == Mode.SLEEP and new_mode != Mode.SLEEP:
            wake_enabled = self._read_register(MCP_CANINTE) & MCP_WAKIF
            if not wake_enabled:
                self._modify_register(MCP_CANINTE, MCP_WAKIF, MCP_WAKIF)
            self._modify_register(MCP_CANINTF, MCP_WAKIF, MCP_WAKIF)
            deadline = time.monotonic() + 0.05
            while self._get_mode() == Mode.SLEEP and time.monotonic() < deadline:
                time.sleep(0.0001)
            if not wake_enabled:
                self._modify_register(MCP_CANINTE, MCP_WAKIF, 0)
            self._modify_register(MCP_CANINTF, MCP_WAKIF, 0)

        # Enter CONFIG first
        deadline = time.monotonic() + 0.05
        while time.monotonic() < deadline:
            self._modify_register(MCP_CANCTRL, CANCTRL_REQOP, Mode.CONFIG)
            if (self._read_register(MCP_CANSTAT) & CANSTAT_OPM) == Mode.CONFIG:
                break
            time.sleep(0.000001)
        else:
            return False

        # Now switch to desired mode
        deadline = time.monotonic() + 0.05
        while time.monotonic() < deadline:
            self._modify_register(MCP_CANCTRL, CANCTRL_REQOP, new_mode)
            if (self._read_register(MCP_CANSTAT) & CANSTAT_OPM) == new_mode:
                return True
            time.sleep(0.000001)

        return False

    def set_config_mode(self) -> bool:
        return self.set_mode(Mode.CONFIG)

    def set_normal_mode(self) -> bool:
        return self.set_mode(Mode.NORMAL)

    def set_loopback_mode(self) -> bool:
        return self.set_mode(Mode.LOOPBACK)

    def set_listen_only_mode(self) -> bool:
        return self.set_mode(Mode.LISTENONLY)

    # ------------------------------------------------------------------
    #  Bit-rate configuration
    # ------------------------------------------------------------------

    def _set_bitrate(self):
        key = (self.clock, self.bitrate)
        if key not in _BITRATE_TABLE:
            return Error.WRONG_BITRATE
        cfg1, cfg2, cfg3 = _BITRATE_TABLE[key]
        self._write_register(MCP_CNF1, cfg1)
        self._write_register(MCP_CNF2, cfg2)
        self._write_register(MCP_CNF3, cfg3)
        return Error.OK

    # ------------------------------------------------------------------
    #  Mask & Filter helpers (from mcp_can_2515.c write_mf)
    # ------------------------------------------------------------------

    def _write_mf(self, addr: int, ext: bool, id_val: int):
        """Write a 4-byte mask/filter register block."""
        buf = [0, 0, 0, 0]
        can_id = id_val & 0xFFFF
        if ext:
            buf[_EID0] = can_id & 0xFF
            buf[_EID8] = (can_id >> 8) & 0xFF
            can_id = (id_val >> 16) & 0xFFFF
            buf[_SIDL] = (can_id & 0x03)
            buf[_SIDL] += ((can_id & 0x1C) << 3) & 0xFF
            buf[_SIDL] |= MCP_TXB_EXIDE_M
            buf[_SIDH] = (can_id >> 5) & 0xFF
        else:
            buf[_SIDL] = ((can_id & 0x07) << 5) & 0xFF
            buf[_SIDH] = (can_id >> 3) & 0xFF
            buf[_EID0] = 0
            buf[_EID8] = 0
        self._spi.xfer2([INSTRUCTION_WRITE, addr] + buf)

    def _init_can_buffers(self):
        """Clear all mask/filter/buffer registers (from init_can_buffer)."""
        self._write_mf(MCP_RXM0SIDH, True, 0x00)
        self._write_mf(MCP_RXM1SIDH, True, 0x00)
        self._write_mf(MCP_RXF0SIDH, True, 0x00)
        self._write_mf(MCP_RXF1SIDH, False, 0x00)
        self._write_mf(MCP_RXF2SIDH, True, 0x00)
        self._write_mf(MCP_RXF3SIDH, False, 0x00)
        self._write_mf(MCP_RXF4SIDH, True, 0x00)
        self._write_mf(MCP_RXF5SIDH, False, 0x00)

        # Clear all three TX buffer control blocks (14 bytes each)
        for base in (MCP_TXB0CTRL, MCP_TXB1CTRL, MCP_TXB2CTRL):
            for offset in range(14):
                self._write_register(base + offset, 0)

    def _set_registers_init(self):
        """Set default register values (from set_registers_init)."""
        self._write_register(MCP_CANINTE, MCP_RX0IF | MCP_RX1IF)
        self._write_register(MCP_BFPCTRL, MCP_BxBFS_MASK | MCP_BxBFE_MASK)
        self._write_register(MCP_TXRTSCTRL, 0x00)
        self._write_register(MCP_RXB0CTRL, MCP_RXB_BUKT_MASK)
        self._write_register(MCP_RXB1CTRL, 0)

    # ------------------------------------------------------------------
    #  Public mask/filter API
    # ------------------------------------------------------------------

    def set_mask(self, num: int, mask: int):
        """Set acceptance mask 0 or 1."""
        if num > 1:
            return
        self.set_config_mode()
        ext = mask > 0x7FF
        addr = MCP_RXM0SIDH if num == 0 else MCP_RXM1SIDH
        self._write_mf(addr, ext, mask)
        self.set_mode(self.mode)

    def set_filter(self, num: int, filt: int):
        """Set acceptance filter 0-5."""
        if num > 5:
            return
        self.set_config_mode()
        ext = filt > 0x7FF
        addr_map = {
            0: MCP_RXF0SIDH, 1: MCP_RXF1SIDH,
            2: MCP_RXF2SIDH, 3: MCP_RXF3SIDH,
            4: MCP_RXF4SIDH, 5: MCP_RXF5SIDH,
        }
        self._write_mf(addr_map[num], ext, filt)
        self.set_mode(self.mode)

    # ------------------------------------------------------------------
    #  Init / Deinit
    # ------------------------------------------------------------------

    def init(self, mode: int = Mode.NORMAL) -> int:
        """
        Initialise MCP2515.  Returns Error.OK on success.
        Corresponds to mcp2515_start() in C code.
        """
        self.mode = mode
        self.reset()

        # Enter config mode
        if not self.set_mode(Mode.CONFIG):
            return Error.FAILINIT

        # Set bitrate
        err = self._set_bitrate()
        if err != Error.OK:
            return err

        # Clear buffers
        self._init_can_buffers()

        # Set default control registers
        self._set_registers_init()

        # Switch to requested operating mode
        if not self.set_mode(mode):
            return Error.FAILINIT

        return Error.OK

    def deinit(self):
        """Reset the chip and release SPI (corresponds to deinit_mcp2515)."""
        try:
            self.reset()
        except Exception:
            pass

    def close(self):
        """Release SPI device."""
        self.deinit()
        try:
            self._spi.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    #  TX  — Write & Send CAN frame
    # ------------------------------------------------------------------

    def _write_id(self, addr: int, frame: CANFrame):
        """Write CAN ID into a TX buffer register block."""
        can_id = frame.can_id
        ext = frame.ext or can_id > 0x7FF
        buf = [0, 0, 0, 0]
        can_id_16 = can_id & 0xFFFF

        if ext:
            buf[_EID0] = can_id_16 & 0xFF
            buf[_EID8] = (can_id_16 >> 8) & 0xFF
            can_id_16 = (can_id >> 16) & 0xFFFF
            buf[_SIDL] = (can_id_16 & 0x03)
            buf[_SIDL] += ((can_id_16 & 0x1C) << 3) & 0xFF
            buf[_SIDL] |= MCP_TXB_EXIDE_M
            buf[_SIDH] = (can_id_16 >> 5) & 0xFF
        else:
            buf[_SIDH] = (can_id_16 >> 3) & 0xFF
            buf[_SIDL] = ((can_id_16 & 0x07) << 5) & 0xFF
            buf[_EID0] = 0
            buf[_EID8] = 0

        self._spi.xfer2([INSTRUCTION_WRITE, addr] + buf)

    def _get_free_tx_buffer(self) -> int:
        """Return TXBnCTRL address of a free TX buffer, or 0xFF if all busy."""
        status = self._get_status()
        if not (status & MCP_STAT_TX0_PENDING):
            return MCP_TXB0CTRL
        if not (status & MCP_STAT_TX1_PENDING):
            return MCP_TXB1CTRL
        if not (status & MCP_STAT_TX2_PENDING):
            return MCP_TXB2CTRL
        return 0xFF

    def send_frame(self, frame: CANFrame) -> int:
        """
        Send a CAN frame.  Returns Error.OK on success.
        Corresponds to send_can_frame() in C code.
        """
        tx_buf = self._get_free_tx_buffer()
        if tx_buf == 0xFF:
            return Error.ALLTXBUSY

        sid_addr = tx_buf + 1  # TXBnSIDH is at TXBnCTRL + 1

        # Write ID
        self._write_id(sid_addr, frame)

        # Write DLC
        dlc = frame.dlc & MCP_DLC_MASK
        if frame.rtr:
            dlc |= MCP_RTR_MASK
        self._write_register(tx_buf + 5, dlc)  # TXBnDLC offset

        # Write data
        data_addr = tx_buf + 6  # TXBnDATA offset
        self._spi.xfer2([INSTRUCTION_WRITE, data_addr] + list(frame.data[:frame.dlc]))

        # Request to send
        self._modify_register(tx_buf, MCP_TXB_TXREQ_M, MCP_TXB_TXREQ_M)

        # Wait for TX complete (timeout ~5 ms)
        deadline = time.monotonic() + 0.005
        while time.monotonic() < deadline:
            ctrl = self._read_register(tx_buf)
            if not (ctrl & MCP_TXB_TXREQ_M):
                return Error.OK
            time.sleep(0.000001)

        return Error.FAILTX

    # ------------------------------------------------------------------
    #  RX  — Check & Read CAN frame
    # ------------------------------------------------------------------

    def check_receive(self) -> int:
        """
        Check if a message is waiting.
        Returns Error.OK if a message is available, Error.NOMSG otherwise.
        """
        status = self._get_status()
        rx_status = status & MCP_STAT_RXIF_MASK

        # Map from READ_STATUS bit positions to CANINTF bits
        if status & MCP_STAT_RX0IF:
            return Error.OK
        if status & MCP_STAT_RX1IF:
            return Error.OK
        return Error.NOMSG

    def _read_frame(self, instruction: int) -> CANFrame:
        """Read a CAN frame using the fast read instruction."""
        # Send instruction + read 4 ID bytes
        tx = [instruction] + [0x00] * 4
        resp = self._spi.xfer2(tx)
        id_bytes = resp[1:5]

        can_id = (id_bytes[_SIDH] << 3) | (id_bytes[_SIDL] >> 5)
        ext = False

        if id_bytes[_SIDL] & MCP_TXB_EXIDE_M:
            can_id = (can_id << 2) | (id_bytes[_SIDL] & 0x03)
            can_id = (can_id << 8) | id_bytes[_EID8]
            can_id = (can_id << 8) | id_bytes[_EID0]
            ext = True

        # Read DLC
        resp2 = self._spi.xfer2([0x00])
        dlc_byte = resp2[0]
        dlc = dlc_byte & MCP_DLC_MASK
        rtr = bool(dlc_byte & MCP_RTR_MASK)

        # Read data bytes
        if dlc > 0:
            data_resp = self._spi.xfer2([0x00] * dlc)
            data = bytes(data_resp)
        else:
            data = b""

        frame = CANFrame(can_id=can_id, data=data, ext=ext, rtr=rtr)
        return frame

    def read_message(self) -> tuple:
        """
        Read a received CAN message.
        Returns (Error code, CANFrame or None).
        Corresponds to read_can_message() in C code.
        """
        status = self._get_status()

        if status & MCP_STAT_RX0IF:
            frame = self._read_rx_buffer(0)
            self._modify_register(MCP_CANINTF, MCP_RX0IF, 0)
            return (Error.OK, frame)
        elif status & MCP_STAT_RX1IF:
            frame = self._read_rx_buffer(1)
            self._modify_register(MCP_CANINTF, MCP_RX1IF, 0)
            return (Error.OK, frame)

        return (Error.NOMSG, None)

    def _read_rx_buffer(self, buf_num: int) -> CANFrame:
        """Read a complete CAN frame from RX buffer 0 or 1."""
        if buf_num == 0:
            base = MCP_RXB0SIDH  # 0x61
        else:
            base = MCP_RXB1SIDH  # 0x71

        # Read 5 bytes: SIDH, SIDL, EID8, EID0, DLC
        header = []
        for i in range(5):
            header.append(self._read_register(base + i))

        # Parse ID
        can_id = (header[0] << 3) | (header[1] >> 5)
        ext = False

        if header[1] & MCP_TXB_EXIDE_M:
            can_id = (can_id << 2) | (header[1] & 0x03)
            can_id = (can_id << 8) | header[2]
            can_id = (can_id << 8) | header[3]
            ext = True

        dlc = header[4] & MCP_DLC_MASK
        rtr = bool(header[4] & MCP_RTR_MASK)

        # Read data
        data_base = base + 5  # RXBnDATA starts 5 bytes after SIDH
        data = bytearray()
        for i in range(min(dlc, 8)):
            data.append(self._read_register(data_base + i))

        return CANFrame(can_id=can_id, data=bytes(data), ext=ext, rtr=rtr)

    # ------------------------------------------------------------------
    #  Error helpers
    # ------------------------------------------------------------------

    def get_error_flags(self) -> int:
        """Read EFLG register."""
        eflg = self._read_register(MCP_EFLG)
        self._modify_register(MCP_EFLG, MCP_EFLG_RX0OVR, 0)
        self._modify_register(MCP_EFLG, MCP_EFLG_RX1OVR, 0)
        return eflg

    def check_error(self) -> int:
        """Return Error.FAIL if bus error, Error.OK otherwise."""
        eflg = self._read_register(MCP_EFLG)
        if eflg & MCP_EFLG_ERRORMASK:
            return Error.FAIL
        return Error.OK
