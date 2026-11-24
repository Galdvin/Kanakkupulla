"""
Transaction Attachment Service:
Safely saves bill photographs, invoice PDFs, and documents to:
%LOCALAPPDATA%\\Kanakkupulla\\attachments\\receipts\\
Creates database linkage to financial_transactions.
"""
from typing import List, Optional, Tuple
from pathlib import Path
import shutil
import uuid
from datetime import datetime
from database.connection import SessionLocal
from database.models import TransactionAttachment, FinancialTransaction
from config.paths import RECEIPTS_DIR, DOCUMENTS_DIR

class AttachmentService:
    @staticmethod
    def attach_file_to_transaction(
        transaction_id: int,
        source_file_path: Path
    ) -> Tuple[bool, str, Optional[TransactionAttachment]]:
        if not source_file_path.exists():
            return False, "File does not exist", None

        # Determine target directory based on file extension
        ext = source_file_path.suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
            target_dir = RECEIPTS_DIR
            file_type = "Image/Receipt"
        else:
            target_dir = DOCUMENTS_DIR
            file_type = "Document"

        target_dir.mkdir(parents=True, exist_ok=True)

        # Unique filename to prevent collisions: e.g. receipt_20261124_uuid.jpg
        unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
        destination_path = target_dir / unique_name

        try:
            shutil.copy2(source_file_path, destination_path)

            db = SessionLocal()
            try:
                txn = db.query(FinancialTransaction).filter_by(id=transaction_id).first()
                if not txn:
                    return False, "Transaction not found", None

                attachment = TransactionAttachment(
                    transaction_id=transaction_id,
                    file_name=source_file_path.name,
                    file_path=str(destination_path),
                    file_type=file_type
                )
                db.add(attachment)
                db.commit()
                db.refresh(attachment)
                db.expunge(attachment)
                return True, "File attached successfully", attachment
            finally:
                db.close()
        except Exception as e:
            return False, f"Failed to attach file: {str(e)}", None

    @staticmethod
    def get_transaction_attachments(transaction_id: int) -> List[TransactionAttachment]:
        db = SessionLocal()
        try:
            attachments = db.query(TransactionAttachment).filter_by(transaction_id=transaction_id).all()
            for a in attachments:
                db.expunge(a)
            return attachments
        finally:
            db.close()
