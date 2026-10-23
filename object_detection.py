import cv2
from ultralytics import YOLO


def detect_objects_in_video(video_source=0, output_file="output.mp4"):
    """
    Detects people, vehicles, and animals in a video stream or video file.
    Detected objects are highlighted with bounding boxes and confidence scores.
    """

    # Load YOLOv8 Nano model
    model = YOLO("yolov8n.pt")

    # Object categories to detect
    allowed_classes = {
        # Person
        "person",

        # Vehicles
        "bicycle",
        "car",
        "motorcycle",
        "bus",
        "train",
        "truck",
        "boat",

        # Animals
        "bird",
        "cat",
        "dog",
        "horse",
        "sheep",
        "cow",
        "elephant",
        "bear",
        "zebra",
        "giraffe"
    }

    # Open webcam or video file
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        print("Error: Could not open video source.")
        return

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Webcam/video sources sometimes report FPS as 0
    if fps <= 0:
        fps = 30

    # Create output video
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        output_file,
        fourcc,
        fps,
        (frame_width, frame_height)
    )

    print(f"Processing video: {video_source}")
    print("Press 'q' to quit.")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("End of video stream or error reading frame.")
            break

        # Run YOLO inference
        results = model(frame, verbose=False)[0]

        # Process detections
        for result in results.boxes:

            # Bounding box
            xyxy = result.xyxy[0].cpu().numpy()

            # Confidence
            conf = float(result.conf[0])

            # Class ID
            cls_id = int(result.cls[0])

            # Class name
            class_name = model.names[cls_id]

            # Only display requested categories
            if class_name in allowed_classes and conf >= 0.5:

                x1, y1, x2, y2 = map(int, xyxy)

                # Draw bounding box
                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                # Detection label
                label = f"{class_name} {conf * 100:.1f}%"

                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

        # Save processed frame
        out.write(frame)

        # Display result
        cv2.imshow("YOLOv8 Object Detection", frame)

        # Press q to stop
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release resources
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    print(f"Video saved to: {output_file}")


if __name__ == "__main__":
    # 0 = default webcam
    detect_objects_in_video(
        video_source=0,
        output_file="output.mp4"
    )
