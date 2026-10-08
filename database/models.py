"""
Data models for the application
Updated with soft delete support and invoice locking
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

@dataclass
class User:
    id: int
    username: str
    password_hash: str
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    role: str = 'admin'
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ShopDetails:
    id: int
    shop_name: str
    address: str
    phone: Optional[str]
    email: Optional[str]
    gst_number: Optional[str]
    logo_path: Optional[str] = None
    owner_name: str = ''
    owner_phone: str = ''
    tagline: Optional[str] = 'AC SALES & SERVICE MANAGEMENT'
    services: Optional[str] = 'Sales | Installation | AMC | Repairing | Gas Refilling'
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Customer:
    id: int
    name: str
    mobile: str
    email: Optional[str]
    address: Optional[str]
    landmark: Optional[str]
    city: Optional[str] = None
    pincode: Optional[str] = None
    customer_type: str = 'Regular'
    notes: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ACBrand:
    id: int
    brand_name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Service:
    id: int
    service_name: str
    description: Optional[str]
    default_rate: Decimal
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Part:
    id: int
    part_name: str
    description: Optional[str]
    default_rate: Decimal
    stock_quantity: int = 0
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Technician:
    id: int
    name: str
    mobile: str
    email: Optional[str]
    address: Optional[str]
    specialization: Optional[str] = None
    commission_rate: Decimal = Decimal('10.00')
    is_active: bool = True
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    joined_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class InvoiceItem:
    id: int
    invoice_id: int
    item_type: str  # 'service' or 'part'
    service_id: Optional[int]
    part_id: Optional[int]
    description: str
    quantity: int = 1
    rate: Decimal = Decimal('0.00')
    amount: Decimal = Decimal('0.00')
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Invoice:
    """
    Invoice model with status tracking and locking
    Status transitions: draft -> final -> paid (locked) or cancelled (locked)
    """
    id: int
    invoice_number: str
    customer_id: int
    ac_brand_id: Optional[int]
    ac_type: str
    star_rating: Optional[str]
    ton_capacity: Optional[str]
    ac_inverter: str
    technician_id: Optional[int]
    subtotal: Decimal
    gst_percentage: Decimal
    gst_amount: Decimal
    total_amount: Decimal
    advance_payment: Decimal
    balance_amount: Decimal
    payment_mode: str
    payment_status: str  # draft, final, paid, cancelled
    notes: Optional[str]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Related objects
    customer: Optional[Customer] = None
    ac_brand: Optional[ACBrand] = None
    technician: Optional[Technician] = None
    items: List[InvoiceItem] = field(default_factory=list)
    
    @property
    def is_locked(self) -> bool:
        """Check if invoice is locked (paid or cancelled)"""
        return self.payment_status in ['paid', 'cancelled']

@dataclass
class Payment:
    id: int
    invoice_id: int
    amount: Decimal
    payment_mode: str
    payment_date: datetime
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TechnicianWork:
    id: int
    technician_id: int
    invoice_id: int
    work_date: datetime
    service_type: str
    amount_collected: Decimal
    pending_amount: Decimal
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class AMCContract:
    """Annual Maintenance Contract"""
    id: int
    contract_number: str
    customer_id: int
    start_date: datetime
    end_date: datetime
    total_amount: Decimal
    paid_amount: Decimal = Decimal('0.00')
    payment_frequency: str = 'yearly'
    status: str = 'active'
    notes: Optional[str] = None
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class DailyLog:
    """Daily Work and Cost Log entry"""
    id: int
    log_date: datetime
    customer_name: str
    customer_mobile: Optional[str] = None
    customer_address: Optional[str] = None
    customer_id: Optional[int] = None
    technician_id: Optional[int] = None
    technician_name: Optional[str] = None
    work_description: Optional[str] = None
    total_billed: Decimal = Decimal('0.00')
    advance_payment: Decimal = Decimal('0.00')
    advance_receiver: str = 'Tech (Cash)'
    final_payment: Decimal = Decimal('0.00')
    final_receiver: str = 'Tech (Cash)'
    total_payment: Decimal = Decimal('0.00')
    pending_amount: Decimal = Decimal('0.00')
    material_cost: Decimal = Decimal('0.00')
    petrol_expense: Decimal = Decimal('0.00')
    total_expense: Decimal = Decimal('0.00')
    payment_status: str = 'Paid'
    payment_mode: str = 'Cash'
    net_profit: Decimal = Decimal('0.00')
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AMCUnit:
    """AC Unit under AMC"""
    id: int
    contract_id: int
    ac_brand: str
    ac_type: Optional[str]
    ac_model: Optional[str]
    serial_number: Optional[str]
    capacity_tonnage: Optional[str]
    installation_year: Optional[int]
    created_at: datetime = field(default_factory=datetime.now)