"""
/****************/  

202418930
Dương Tùng Lâm

/****************/  

"""

"""
HỆ THỐNG QUẢN LÝ THIẾT BỊ VÀ HỢP ĐỒNG BẢO TRÌ
================================================

Tóm tắt thiết kế
----------------
* Device (lớp trừu tượng)  <-- Computer, Printer, Projector : KẾ THỪA ("is-a").
* INetworkable (interface) : Năng lực độc lập với cây kế thừa, vì máy tính luôn có mạng, chỉ một số máy in có mạng, còn máy chiếu thì không.
* LabRoom "có" nhiều Device : Kết tập (aggregation), không phải hợp thành (composition) vì thiết bị tồn tại độc lập với phòng.

Phương án cho "Chỉ một số máy in có mạng"
-----------------------------------------
Chọn: tách NetworkPrinter kế thừa Printer và thực thi INetworkable.
Trade-off:
  - Ưu điểm: thể hiện đúng "máy in mạng là một loại máy in", dùng được đa hình qua cả Printer lẫn INetworkable, 
    không có thuộc tính/phương thức mạng "chết" ở máy in thường, và kiểm tra kiểu (isinstance INetworkable) rất tự nhiên.
  - Nhược điểm: thêm một lớp; nếu sau này một máy in thường được nâng cấp thêm card mạng thì phải tạo đối tượng mới (kế thừa là quan hệ cố định lúc tạo).
  - Phương án kết tập một thành phần NetworkModule linh hoạt hơn khi cần thay đổi lúc chạy, nhưng phức tạp hơn mức cần thiết ở phiên bản hiện tại.

Quan hệ giữa LabRoom và Device là kết tập hay hợp thành? Giải thích dựa trên vòng đời của 
hai đối tượng.
--------------------------------------------------------
Thiết bị có vòng đời độc lập với phòng: nó tồn tại khi chưa được phân bổ phòng, có thể bị gỡ khỏi phòng rồi chuyển sang phòng khác, 
và khi phòng bị xóa thì thiết bị vẫn còn trong hệ thống. Nếu là hợp thành, thiết bị sẽ bị hủy cùng phòng.
"""


from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional


# ======================================================================
# Enum
# ======================================================================
class DeviceStatus(Enum):
    ACTIVE = "Active"
    UNDER_MAINTENANCE = "UnderMaintenance"
    RETIRED = "Retired"


class PrinterType(Enum):
    LASER = "Laser"
    INKJET = "Phun"


# ======================================================================
# Interface INetworkable
# ======================================================================
class INetworkable(ABC):
    """Năng lực kết nối mạng, độc lập với cây kế thừa Device."""

    @property
    @abstractmethod
    def ip_address(self) -> Optional[str]:
        ...

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        ...

    @abstractmethod
    def connect(self, ip_address: str) -> None:
        ...

    @abstractmethod
    def disconnect(self) -> None:
        ...


class _ConnectionState:
    """Thành phần nhỏ giữ trạng thái kết nối, dùng chung cho các lớp INetworkable
    để tránh lặp mã (Computer và NetworkPrinter dùng chung qua kết tập)."""

    def __init__(self) -> None:
        self._ip: Optional[str] = None
        self._connected = False

    @property
    def ip(self) -> Optional[str]:
        return self._ip

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self, ip_address: str) -> None:
        if ip_address is None or not ip_address.strip():
            raise ValueError("Địa chỉ IP không được rỗng.")
        if self._connected:
            raise RuntimeError("Thiết bị đang kết nối, không thể kết nối lại.")
        self._ip = ip_address.strip()
        self._connected = True

    def disconnect(self) -> None:
        if not self._connected:
            raise RuntimeError("Thiết bị chưa kết nối.")
        self._ip = None  # không còn địa chỉ IP hoạt động
        self._connected = False


# ======================================================================
# Lớp trừu tượng Device
# ======================================================================
class Device(ABC):
    MAINTENANCE_AGE_YEARS = 5

    def __init__(self, device_id: str, name: str, year_in_use: int,
                 purchase_price: Decimal,
                 status: DeviceStatus = DeviceStatus.ACTIVE) -> None:
        if device_id is None or not device_id.strip():
            raise ValueError("Mã thiết bị không được rỗng.")
        if purchase_price is None or purchase_price <= 0:
            raise ValueError("Giá mua phải lớn hơn 0.")
        if year_in_use > datetime.now().year:
            raise ValueError("Năm đưa vào sử dụng không được lớn hơn năm hiện tại.")
        if year_in_use <= 0:
            raise ValueError("Năm đưa vào sử dụng không hợp lệ.")
        if name is None or not name.strip():
            raise ValueError("Tên thiết bị không được rỗng.")

        self._device_id = device_id.strip()   # chỉ gán ở constructor
        self.name = name.strip()
        self._year_in_use = year_in_use
        self._purchase_price = purchase_price
        self.status = status

    # --- Mã thiết bị: ---
    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def year_in_use(self) -> int:
        return self._year_in_use

    @property
    def purchase_price(self) -> Decimal:
        return self._purchase_price

    @property
    def age(self) -> int:
        """Số năm đã sử dụng."""
        return datetime.now().year - self._year_in_use

    @property
    def is_older_than_limit(self) -> bool:
        return self.age > self.MAINTENANCE_AGE_YEARS

    @abstractmethod
    def calculate_maintenance_cost(self) -> Decimal:
        """Chi phí bảo trì dự kiến trong một năm."""

    def __str__(self) -> str:
        return (f"[{self.__class__.__name__}] Mã: {self.device_id} | Tên: {self.name} | "
                f"Năm SD: {self.year_in_use} | Giá mua: {fmt_money(self.purchase_price)} | "
                f"Trạng thái: {self.status.value}")


# ======================================================================
# Các lớp dẫn xuất
# ======================================================================
class Computer(Device, INetworkable):
    def __init__(self, device_id: str, name: str, year_in_use: int,
                 purchase_price: Decimal, ram_gb: int, cpu: str,
                 has_discrete_gpu: bool,
                 status: DeviceStatus = DeviceStatus.ACTIVE) -> None:
        super().__init__(device_id, name, year_in_use, purchase_price, status)
        if ram_gb <= 0:
            raise ValueError("Dung lượng RAM phải lớn hơn 0.")
        if cpu is None or not cpu.strip():
            raise ValueError("Loại bộ xử lý không được rỗng.")
        self.ram_gb = ram_gb
        self.cpu = cpu.strip()
        self.has_discrete_gpu = has_discrete_gpu
        self._conn = _ConnectionState()

    # --- INetworkable ---
    @property
    def ip_address(self) -> Optional[str]:
        return self._conn.ip

    @property
    def is_connected(self) -> bool:
        return self._conn.connected

    def connect(self, ip_address: str) -> None:
        self._conn.connect(ip_address)

    def disconnect(self) -> None:
        self._conn.disconnect()

    # --- Device ---
    def calculate_maintenance_cost(self) -> Decimal:
        rate = Decimal("0.05")
        if self.has_discrete_gpu:
            rate += Decimal("0.02")
        if self.is_older_than_limit:
            rate += Decimal("0.01")
        return self.purchase_price * rate

    def __str__(self) -> str:
        return (f"{super().__str__()} | RAM: {self.ram_gb}GB | CPU: {self.cpu} | "
                f"GPU rời: {'Có' if self.has_discrete_gpu else 'Không'} | "
                f"Mạng: {'Đã kết nối ' + str(self.ip_address) if self.is_connected else 'Chưa kết nối'}")


class Printer(Device):
    """Máy in thường (không có mạng)."""

    def __init__(self, device_id: str, name: str, year_in_use: int,
                 purchase_price: Decimal, printer_type: PrinterType,
                 pages_printed: int, is_color: bool,
                 status: DeviceStatus = DeviceStatus.ACTIVE) -> None:
        super().__init__(device_id, name, year_in_use, purchase_price, status)
        if pages_printed < 0:
            raise ValueError("Số trang đã in không được âm.")
        self.printer_type = printer_type
        self.pages_printed = pages_printed
        self.is_color = is_color  # bổ sung: cần để xác định phụ phí máy in màu

    def calculate_maintenance_cost(self) -> Decimal:
        cost = self.purchase_price * Decimal("0.04")
        if self.pages_printed > 100_000:
            cost += Decimal("500000")
        if self.is_color:
            cost += Decimal("300000")
        return cost

    def __str__(self) -> str:
        return (f"{super().__str__()} | Loại: {self.printer_type.value} | "
                f"Đã in: {self.pages_printed:,} trang | "
                f"Màu: {'Có' if self.is_color else 'Không'}")


class NetworkPrinter(Printer, INetworkable):
    """Máy in có hỗ trợ mạng: là một Printer và có năng lực INetworkable."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._conn = _ConnectionState()

    @property
    def ip_address(self) -> Optional[str]:
        return self._conn.ip

    @property
    def is_connected(self) -> bool:
        return self._conn.connected

    def connect(self, ip_address: str) -> None:
        self._conn.connect(ip_address)

    def disconnect(self) -> None:
        self._conn.disconnect()

    def __str__(self) -> str:
        return (f"{super().__str__()} | Hỗ trợ mạng: Có | "
                f"Mạng: {'Đã kết nối ' + str(self.ip_address) if self.is_connected else 'Chưa kết nối'}")


class Projector(Device):
    def __init__(self, device_id: str, name: str, year_in_use: int,
                 purchase_price: Decimal, brightness_lumen: int,
                 lamp_hours: int,
                 status: DeviceStatus = DeviceStatus.ACTIVE) -> None:
        super().__init__(device_id, name, year_in_use, purchase_price, status)
        if brightness_lumen <= 0:
            raise ValueError("Độ sáng phải lớn hơn 0.")
        if lamp_hours < 0:
            raise ValueError("Số giờ sử dụng bóng đèn không được âm.")
        self.brightness_lumen = brightness_lumen
        self.lamp_hours = lamp_hours

    def calculate_maintenance_cost(self) -> Decimal:
        cost = self.purchase_price * Decimal("0.03")
        if self.lamp_hours > 3000:
            cost += Decimal("1500000")
        return cost

    def __str__(self) -> str:
        return (f"{super().__str__()} | Độ sáng: {self.brightness_lumen} lumen | "
                f"Giờ bóng đèn: {self.lamp_hours:,}h")


# ======================================================================
# Lớp LabRoom
# ======================================================================
class LabRoom:
    def __init__(self, room_id: str, name: str, capacity: int) -> None:
        if room_id is None or not room_id.strip():
            raise ValueError("Mã phòng không được rỗng.")
        if name is None or not name.strip():
            raise ValueError("Tên phòng không được rỗng.")
        if capacity <= 0:
            raise ValueError("Sức chứa phải lớn hơn 0.")
        self.room_id = room_id.strip()
        self.name = name.strip()
        self.capacity = capacity
        self._devices: list[Device] = []

    @property
    def devices(self) -> list[Device]:
        return list(self._devices)  # trả bản sao để bảo vệ danh sách bên trong

    def add_device(self, device: Device) -> None:
        if device is None:
            raise ValueError("Thiết bị không được null.")
        if not isinstance(device, Device):
            raise TypeError("Đối tượng thêm vào phải là Device.")
        if self.find_device(device.device_id) is not None:
            raise ValueError(f"Phòng {self.room_id} đã có thiết bị mã '{device.device_id}'.")
        self._devices.append(device)

    def remove_device(self, device_id: str) -> bool:
        device = self.find_device(device_id)
        if device is None:
            return False
        self._devices.remove(device)  # chỉ gỡ khỏi phòng, thiết bị vẫn tồn tại
        return True

    def find_device(self, device_id: str) -> Optional[Device]:
        for d in self._devices:
            if d.device_id == device_id:
                return d
        return None

    def calculate_annual_maintenance_cost(self) -> Decimal:
        return sum((d.calculate_maintenance_cost() for d in self._devices), Decimal(0))

    def get_devices_requiring_maintenance(self) -> list[Device]:
        return [d for d in self._devices
                if d.status == DeviceStatus.UNDER_MAINTENANCE or d.is_older_than_limit]

    def __str__(self) -> str:
        return (f"Phòng {self.room_id} - {self.name} | Sức chứa: {self.capacity} | "
                f"Số thiết bị: {len(self._devices)}")


# ======================================================================
# Tiện ích
# ======================================================================
def fmt_money(value: Decimal) -> str:
    return f"{value:,.0f} đồng"


def input_text(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s:
            return s
        print("  ! Không được để trống.")


def input_int(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("  ! Vui lòng nhập số nguyên.")


def input_decimal(prompt: str) -> Decimal:
    while True:
        try:
            return Decimal(input(prompt).strip().replace(",", ""))
        except InvalidOperation:
            print("  ! Vui lòng nhập một số hợp lệ.")


def input_yes_no(prompt: str) -> bool:
    while True:
        s = input(prompt + " (c/k): ").strip().lower()
        if s in ("c", "co", "có", "y", "yes"):
            return True
        if s in ("k", "khong", "không", "n", "no"):
            return False
        print("  ! Nhập 'c' (có) hoặc 'k' (không).")


# ======================================================================
# Main
# ======================================================================
class App:
    def __init__(self) -> None:
        # Thiết bị tồn tại độc lập với phòng -> lưu trong kho riêng
        self.devices: dict[str, Device] = {}
        self.rooms: dict[str, LabRoom] = {}

    def load_test_data(self) -> None:
        """Nạp bộ dữ liệu mẫu để kiểm thử các yêu cầu chính của hệ thống."""
        if self.devices or self.rooms:
            raise RuntimeError("Chỉ nạp bộ dữ liệu kiểm thử khi hệ thống đang trống.")

        current_year = datetime.now().year
        test_devices: list[Device] = [
            Computer(
                "PC-01", "Máy tính văn phòng", current_year - 2,
                Decimal("18000000"), 16, "Intel Core i5", False,
            ),
            Computer(
                "PC-02", "Máy tính đồ họa", current_year - 3,
                Decimal("32000000"), 32, "Intel Core i7", True,
            ),
            Printer(
                "PR-01", "Máy in laser đen trắng", current_year - 2,
                Decimal("6500000"), PrinterType.LASER, 45000, False,
            ),
            NetworkPrinter(
                "PR-02", "Máy in laser mạng", current_year - 4,
                Decimal("12000000"), PrinterType.LASER, 125000, True,
            ),
            Projector(
                "PJ-01", "Máy chiếu phòng học", current_year - 4,
                Decimal("22000000"), 4000, 3500,
            ),
        ]
        self.devices = {device.device_id: device for device in test_devices}

        room_a = LabRoom("LAB-01", "Phòng thực hành lập trình", 30)
        room_b = LabRoom("LAB-02", "Phòng thực hành đồ họa", 25)
        self.rooms = {room_a.room_id: room_a, room_b.room_id: room_b}

        for device_id in ("PC-01", "PC-02", "PR-01"):
            room_a.add_device(self.devices[device_id])
        for device_id in ("PR-02", "PJ-01"):
            room_b.add_device(self.devices[device_id])

    # ---------- helper ----------
    def _room_of(self, device_id: str) -> Optional[LabRoom]:
        for room in self.rooms.values():
            if room.find_device(device_id) is not None:
                return room
        return None

    def _ask_new_device_common(self):
        while True:
            device_id = input_text("Mã thiết bị: ")
            if device_id in self.devices:
                print("  ! Mã thiết bị đã tồn tại trong hệ thống.")
            else:
                break
        name = input_text("Tên thiết bị: ")
        year = input_int("Năm đưa vào sử dụng: ")
        price = input_decimal("Giá mua (đồng): ")
        return device_id, name, year, price

    def _ask_room(self) -> Optional[LabRoom]:
        if not self.rooms:
            print("  ! Chưa có phòng nào.")
            return None
        room_id = input_text("Mã phòng: ")
        room = self.rooms.get(room_id)
        if room is None:
            print("  ! Không tìm thấy phòng.")
        return room

    def _ask_device(self) -> Optional[Device]:
        device_id = input_text("Mã thiết bị: ")
        device = self.devices.get(device_id)
        if device is None:
            print("  ! Không tìm thấy thiết bị.")
        return device

    # ---------- Chức năng ----------
    def add_computer(self) -> None:
        device_id, name, year, price = self._ask_new_device_common()
        ram = input_int("Dung lượng RAM (GB): ")
        cpu = input_text("Loại bộ xử lý: ")
        gpu = input_yes_no("Có GPU rời?")
        self.devices[device_id] = Computer(device_id, name, year, price, ram, cpu, gpu)
        print("  => Đã thêm máy tính.")

    def add_printer(self) -> None:
        device_id, name, year, price = self._ask_new_device_common()
        while True:
            t = input("Loại máy in (1: Laser, 2: Phun): ").strip()
            if t in ("1", "2"):
                break
            print("  ! Chọn 1 hoặc 2.")
        ptype = PrinterType.LASER if t == "1" else PrinterType.INKJET
        pages = input_int("Số trang đã in: ")
        color = input_yes_no("Là máy in màu?")
        network = input_yes_no("Có hỗ trợ mạng?")
        cls = NetworkPrinter if network else Printer
        self.devices[device_id] = cls(device_id, name, year, price, ptype, pages, color)
        print("  => Đã thêm máy in" + (" (máy in mạng)." if network else "."))

    def add_projector(self) -> None:
        device_id, name, year, price = self._ask_new_device_common()
        lumen = input_int("Độ sáng (lumen): ")
        hours = input_int("Số giờ đã sử dụng bóng đèn: ")
        self.devices[device_id] = Projector(device_id, name, year, price, lumen, hours)
        print("  => Đã thêm máy chiếu.")

    def create_room(self) -> None:
        room_id = input_text("Mã phòng: ")
        if room_id in self.rooms:
            print("  ! Mã phòng đã tồn tại.")
            return
        name = input_text("Tên phòng: ")
        capacity = input_int("Sức chứa: ")
        self.rooms[room_id] = LabRoom(room_id, name, capacity)
        print("  => Đã tạo phòng.")

    def add_device_to_room(self) -> None:
        room = self._ask_room()
        if room is None:
            return
        device = self._ask_device()
        if device is None:
            return
        current = self._room_of(device.device_id)
        if current is not None and current is not room:
            print(f"  ! Thiết bị đang ở phòng {current.room_id}. Hãy gỡ khỏi phòng đó trước.")
            return
        room.add_device(device)  # ném lỗi nếu trùng mã
        print("  => Đã thêm thiết bị vào phòng.")

    def remove_device_from_room(self) -> None:
        room = self._ask_room()
        if room is None:
            return
        device_id = input_text("Mã thiết bị cần gỡ: ")
        if room.remove_device(device_id):
            print("  => Đã gỡ thiết bị khỏi phòng (thiết bị vẫn còn trong hệ thống).")
        else:
            print("  ! Phòng không có thiết bị này.")

    def list_all_devices(self) -> None:
        if not self.devices:
            print("  (Chưa có thiết bị nào)")
            return
        for d in self.devices.values():
            room = self._room_of(d.device_id)
            print(f"- {d}\n    Phòng: {room.room_id if room else 'Chưa phân bổ'}")

    def list_room_devices(self) -> None:
        room = self._ask_room()
        if room is None:
            return
        print(room)
        if not room.devices:
            print("  (Phòng chưa có thiết bị)")
        for d in room.devices:
            print(f"- {d}")

    def room_maintenance_cost(self) -> None:
        room = self._ask_room()
        if room is None:
            return
        print(f"Tổng chi phí bảo trì dự kiến/năm của phòng {room.room_id}: "
              f"{fmt_money(room.calculate_annual_maintenance_cost())}")
        for d in room.devices:
            print(f"  - {d.device_id} ({d.name}): {fmt_money(d.calculate_maintenance_cost())}")

    def room_devices_need_maintenance(self) -> None:
        room = self._ask_room()
        if room is None:
            return
        items = room.get_devices_requiring_maintenance()
        if not items:
            print("  (Không có thiết bị nào cần bảo trì)")
        for d in items:
            print(f"- {d}")

    def change_status(self) -> None:
        device = self._ask_device()
        if device is None:
            return
        while True:
            s = input("Trạng thái mới (1: Active, 2: UnderMaintenance, 3: Retired): ").strip()
            if s in ("1", "2", "3"):
                break
            print("  ! Chọn 1, 2 hoặc 3.")
        device.status = {"1": DeviceStatus.ACTIVE,
                         "2": DeviceStatus.UNDER_MAINTENANCE,
                         "3": DeviceStatus.RETIRED}[s]
        print("  => Đã cập nhật trạng thái.")

    def connect_device(self) -> None:
        device = self._ask_device()
        if device is None:
            return
        if not isinstance(device, INetworkable):
            print("  ! Thiết bị này không có khả năng kết nối mạng.")
            return
        ip = input("Địa chỉ IP: ")
        device.connect(ip)
        print(f"  => Đã kết nối, IP: {device.ip_address}")

    def disconnect_device(self) -> None:
        device = self._ask_device()
        if device is None:
            return
        if not isinstance(device, INetworkable):
            print("  ! Thiết bị này không có khả năng kết nối mạng.")
            return
        device.disconnect()
        print("  => Đã ngắt kết nối.")

    def list_network_devices(self) -> None:
        """Duyệt qua kiểu INetworkable, không phụ thuộc lớp cụ thể."""
        networkables = [d for d in self.devices.values() if isinstance(d, INetworkable)]
        if not networkables:
            print("  (Chưa có thiết bị mạng nào)")
            return
        for n in networkables:
            state = f"Đã kết nối (IP: {n.ip_address})" if n.is_connected else "Chưa kết nối"
            print(f"- {n.device_id} ({n.name}): {state}")  # type: ignore[attr-defined]

    def load_test_data_from_menu(self) -> None:
        self.load_test_data()
        print("  => Đã nạp bộ dữ liệu kiểm thử.")

    def run(self) -> None:
        actions = {
            "1": ("Thêm máy tính", self.add_computer),
            "2": ("Thêm máy in", self.add_printer),
            "3": ("Thêm máy chiếu", self.add_projector),
            "4": ("Tạo phòng thực hành", self.create_room),
            "5": ("Thêm thiết bị vào phòng", self.add_device_to_room),
            "6": ("Gỡ thiết bị khỏi phòng", self.remove_device_from_room),
            "7": ("Danh sách tất cả thiết bị", self.list_all_devices),
            "8": ("Danh sách thiết bị trong phòng", self.list_room_devices),
            "9": ("Tổng chi phí bảo trì dự kiến của phòng", self.room_maintenance_cost),
            "10": ("Liệt kê thiết bị cần bảo trì của phòng", self.room_devices_need_maintenance),
            "11": ("Đổi trạng thái thiết bị", self.change_status),
            "12": ("Kết nối mạng cho thiết bị", self.connect_device),
            "13": ("Ngắt kết nối mạng", self.disconnect_device),
            "14": ("Duyệt các thiết bị mạng (INetworkable)", self.list_network_devices),
            "15": ("Nạp bộ dữ liệu kiểm thử", self.load_test_data_from_menu),
            "0": ("Thoát", None),
        }
        while True:
            print("\n===== QUẢN LÝ THIẾT BỊ PHÒNG THỰC HÀNH =====")
            for key, (label, _) in actions.items():
                print(f"{key:>2}. {label}")
            choice = input("Chọn chức năng: ").strip()
            if choice == "0":
                print("Tạm biệt!")
                break
            action = actions.get(choice)
            if action is None:
                print("  ! Lựa chọn không hợp lệ.")
                continue
            try:
                action[1]()
            except (ValueError, TypeError, RuntimeError) as ex:
                print(f"  ! Lỗi: {ex}")


if __name__ == "__main__":
    App().run()
