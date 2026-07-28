import os
from google.cloud import firestore

# Uses Application Default Credentials (ADC) or project default
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "flash-gasket-486800-p9")
db = firestore.Client(project=PROJECT_ID)

def cleanup_leftover_test_users():
    users_ref = db.collection("users")
    print("🔍 Scanning Firestore 'users' collection for test profiles...")

    # Fetch all documents in the users collection
    docs = users_ref.stream()
    
    deleted_count = 0
    batch = db.batch()
    batch_count = 0

    for doc in docs:
        doc_id = doc.id
        # Target profiles created by load tests or simulators
        if doc_id.startswith("locust_user_") or doc_id.startswith("test_user_") or doc_id.startswith("user_"):
            print(f"🗑️ Queueing deletion for: {doc_id}")
            batch.delete(doc.reference)
            deleted_count += 1
            batch_count += 1

            # Firestore batches are capped at 500 operations per commit
            if batch_count >= 400:
                batch.commit()
                print(f"✅ Committed batch deletion of {batch_count} users...")
                batch = db.batch()
                batch_count = 0

    # Commit remaining items in final batch
    if batch_count > 0:
        batch.commit()
        print(f"✅ Final batch commit completed.")

    print(f"\n🎉 Cleanup finished! Total test documents deleted: {deleted_count}")

if __name__ == "__main__":
    cleanup_leftover_test_users()