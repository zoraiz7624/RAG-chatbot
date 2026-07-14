import cv2  # computer vision library
import numpy as np
from insightface.app import FaceAnalysis  # AI face recognition model

face_app = FaceAnalysis()
face_app.prepare(ctx_id=0)


def get_face_embedding(image_path: str):
    """
    Loads an image from disk, detects a face, and returns its embedding
    as a plain Python list (so it's safe to store in MongoDB).
    Raises ValueError if the image can't be read or no face is found.
    """
    frame = cv2.imread(image_path)
    if frame is None:
        raise ValueError("Could not read the uploaded image")

    faces = face_app.get(frame)
    if len(faces) == 0:
        raise ValueError("No face detected in the image")

    return faces[0].embedding.tolist()


def find_matching_user(live_embedding, users_collection, threshold: float = 0.6):
    """
    Compares the given embedding against every user with a stored
    face_embedding in the collection. Returns (username, best_score)
    for the best match above threshold, or (None, best_score) if no
    user matches closely enough.
    """
    live = np.array(live_embedding)
    best_username = None
    best_score = -1.0

    for user in users_collection.find({"face_embedding": {"$exists": True}}):
        saved = np.array(user["face_embedding"])
        score = float(
            np.dot(live, saved) / (np.linalg.norm(live) * np.linalg.norm(saved))
        )
        if score > best_score:
            best_score = score
            best_username = user["username"]

    if best_score >= threshold:
        return best_username, best_score
    return None, best_score


if __name__ == "__main__":
    # Standalone webcam test - not used by the deployed chatbot.
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    print("Webcam test mode. Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.imshow("Face Test", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
