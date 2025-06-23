from app.models.database import Base, engine
from app.models.models import DailyMarketingData, Campaign, ExternalFactor, AttributionResult

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")