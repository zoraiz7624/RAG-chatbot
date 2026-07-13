import cv2 #computer vision library
import numpy as np
from insightface.app import FaceAnalysis #AI face recognition model: Detects, aligns and extracts AI face embeddings

face_app = FaceAnalysis() #Loads an AI model trained on millions of faces
face_app.prepare(ctx_id=0) #initializes the model

SAVED_FACE_DATABASE = None

def detect_face_coordinates(frame):
    
    # Scans a frame to locate human faces and return a list of coordinates marking where a face boundary starts and ends
    
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # converts color image to greyscale image
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')# using open cvs's pre trained model to create face detector
    face_boxes = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5)#actual detection. scale factor means the detector repeatedly shrinks the scanning window
    return face_boxes

    
def get_face_embedding(frame):
    
    #Generates an AI face embedding from an image.
    

    faces = face_app.get(frame)

    if len(faces) == 0:
        return None

    return faces[0].embedding
    
def verify_embedding(live_embedding, saved_embedding, threshold=0.6):
    
    #Compare two face embeddings using cosine similarity
    #Returns True if they belong to the same person
    

    if live_embedding is None or saved_embedding is None:
        return False

    similarity = np.dot(live_embedding, saved_embedding) / ( #cosine similarity: how similar 2 vectors are
        np.linalg.norm(live_embedding) * np.linalg.norm(saved_embedding) #calculates the length (magnitude) of each embedding vector
    )

    print(f"Similarity Score: {similarity:.3f}")

    return similarity >= threshold


    
    
  


if __name__ == "__main__": # everything below is a testing program not used by the chatbot
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    print("---------------------------------------------------------")
    print("Webcam started.")
    print("1. Look at the camera and press 's' to SAVE your face profile.")
    print("2. Press 'q' on your window to close the program.")
    print("---------------------------------------------------------")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame from camera")
            break

        coordinates = detect_face_coordinates(frame)
        key = cv2.waitKey(1) & 0xFF

        if len(coordinates) > 0:
            # Generate the face embedding for the current frame
            current_face = get_face_embedding(frame)
            
            #SIMULATION: SIGN-UP (Press 's')
            if key == ord('s') and current_face is not None:
                SAVED_FACE_DATABASE = current_face
                print("\n[SUCCESS] Face profile saved to memory! Beginning live match validation...\n")

            #SIMULATION: AUTHENTICATION LOGIN
            if SAVED_FACE_DATABASE is not None:
                is_authorized = verify_embedding(current_face, SAVED_FACE_DATABASE, threshold=0.70)
                
                if is_authorized:
                    box_color = (0, 255, 0) # Green = Access Granted
                    status_text = "ACCESS GRANTED"
                else:
                    box_color = (0, 0, 255) # Red = Unauthorized/Intruder
                    status_text = "UNKNOWN USER"
            else:
                box_color = (255, 255, 0) # Yellow = Not Registered Yet
                status_text = "Press 's' to Register"

            # Draw bounding box and text on feed
            for (x, y, w, h) in coordinates:
                cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
                cv2.putText(frame, status_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
        else:
            print("Scanning... No face detected.")

        cv2.imshow("Main Camera Feed", frame)
        
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()