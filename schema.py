from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class TargetSystem(str, Enum):
    SAP_S4HANA = "SAP S/4HANA"
    SAP_SUCCESSFACTORS = "SAP SuccessFactors"
    MICROSOFT_365 = "Microsoft 365"
    ENTRA_ID = "Active Directory / Entra ID"
    SERVICENOW = "ServiceNow"
    TEAMCENTER = "Siemens Teamcenter"
    CATIA = "CATIA V6"
    POLARION = "Polarion ALM"
    OPCENTER = "Opcenter MES"
    SCADA = "Ignition SCADA"
    QDAS = "Q-DAS"
    EDI = "EDI Gateway (OpenText)"
    TISAX = "TISAX Compliance Portal"
    SHAREPOINT = "SharePoint Online"
    POWER_BI = "Power BI"
    COUPA = "Coupa"
    TRANSPOREON = "Transporeon"
    KRONOS = "Kronos / UKG Workforce"
    UNKNOWN = "UNKNOWN"

class SupportQueue(str, Enum):
    L1_ACCESS = "L1_ACCESS"
    L1_WORKSTATIONS = "L1_WORKSTATIONS"
    L2_SAP_FINANCE = "L2_SAP_FINANCE"
    L2_HR_SERVICES = "L2_HR_SERVICES"
    L2_ITSM_SUPPORT = "L2_ITSM_SUPPORT"
    L2_PLM_SUPPORT = "L2_PLM_SUPPORT"
    L2_CATIA_SUPPORT = "L2_CATIA_SUPPORT"
    L2_ALM_SUPPORT = "L2_ALM_SUPPORT"
    L2_MES_SERVICE = "L2_MES_SERVICE"
    L2_PLANT_BRNO = "L2_PLANT_BRNO"
    L2_EDI = "L2_EDI"
    L2_DATA_HUB = "L2_DATA_HUB"
    L2_PLANT_WOLFSBURG = "L2_PLANT_WOLFSBURG"
    L2_TIME_ATTENDANCE = "L2_TIME_ATTENDANCE"
    L3_ACCELERA = "L3_ACCELERA"
    L3_MICROSOFT_INCIDENTS = "L3_MICROSOFT_INCIDENTS"
    L3_SECUREEDGE = "L3_SECUREEDGE"
    L3_CATIA_INCIDENTS = "L3_CATIA_INCIDENTS"
    L3_BLUEWIRE = "L3_BLUEWIRE"
    L3_MES_INCIDENTS = "L3_MES_INCIDENTS"
    L3_INFRASTRUCTURE = "L3_INFRASTRUCTURE"
    BOUNCE_QUEUE = "BOUNCE_QUEUE"

class TicketEvaluation(BaseModel):
    is_actionable: bool = Field(
        description="True if ticket has enough context to act; False if missing critical system or reproduction steps."
    )
    bounce_reason: Optional[str] = Field(
        default=None,
        description="Explanation sent back to user if actionable is False."
    )
    missing_fields: List[str] = Field(
        default=[],
        description="Explicit list of missing data items (e.g. system_name, error_code)."
    )
    target_system: TargetSystem = Field(
        description="Identified application from the catalog or UNKNOWN."
    )
    assigned_queue: SupportQueue = Field(
        description="Target enterprise support queue or BOUNCE_QUEUE if non-actionable."
    )
    summary: str = Field(
        description="1-sentence objective summary of the issue."
    )