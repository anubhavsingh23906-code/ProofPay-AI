
from sqlalchemy import Column, String, Float, Integer, JSON
from database import Base


class Task(Base):
    __tablename__ = "tasks"
    

    # Unique task ID
    task_id = Column(String, primary_key=True, index=True)

    # Basic task information
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)

    budget = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    deadline_days = Column(Integer, nullable=False)

    # Workflow status
    status = Column(String, default="draft")

    # Store workflow information
    agreement = Column(JSON, nullable=True)
    agreement_decision = Column(JSON, nullable=True)
    submission = Column(JSON, nullable=True)
    verification = Column(JSON, nullable=True)
    client_review = Column(JSON, nullable=True)
    payment = Column(JSON, nullable=True)
