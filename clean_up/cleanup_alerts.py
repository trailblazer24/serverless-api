import os
from google.cloud import firestore

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "flash-gasket-486800-p9")
db = firestore.Client(project=PROJECT_ID)

def purge_system_alerts():
    alerts_ref = db.collection("system_alerts")
    print("🔍 Scanning Firestore 'system_alerts' collection in safe batches...")

    deleted_count = 0
    batch_size = 100  # Pull small batches to avoid timeouts

    while True:
        # Fetch a small chunk of documents
        docs = list(alerts_ref.limit(batch_size).stream())
        if not docs:
            break  # Exit loop when collection is empty

        batch = db.batch()
        for doc in docs:
            print(f"🗑️ Queueing alert deletion: {doc.id}")
            batch.delete(doc.reference)
            deleted_count += 1

        # Commit the batch deletion
        batch.commit()
        print(f"✅ Successfully purged a batch of {len(docs)} alerts (Total so far: {deleted_count})...")

    print(f"\n🎉 Alert cleanup complete! Total system alert documents deleted: {deleted_count}")

if __name__ == "__main__":
    purge_system_alerts()