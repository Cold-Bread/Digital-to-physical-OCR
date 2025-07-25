import { useEffect, useState } from "react";
import { usePatientStore } from "../store/globalStore";

function ImageViewer() {
	const [originalImage, setOriginalImage] = useState<string | null>(null);
	const { setOcrOutput, setEditableText } = usePatientStore();

	useEffect(() => {
		const handleKeyPress = (e: KeyboardEvent) => {
			if (e.key === "Enter") {
				setOriginalImage("https://placehold.co/400x300?text=Original+Img");

				// simulate backend result
				const patient = {
					name: "John Doe",
					dob: "1990-01-01",
					last_visit: "2025-07-22",
					taken_from: "Hospital A",
					placed_in: "Shred Bin 3",
					to_shred: true,
					date_shredded: undefined,
				};

				setOcrOutput(patient);
				setEditableText(patient);
			}
		};

		document.addEventListener("keydown", handleKeyPress);
		return () => document.removeEventListener("keydown", handleKeyPress);
	}, []);

	return (
		<div className="img-container">
			<div className="img-block">
				<h2>Original Image</h2>
				<img
					id="originalImage"
					src="https://placehold.co/400x300?text=Placeholder"
					alt="Original Placeholder"
				/>
			</div>

			<div className="img-block">
				<h2>Enhanced Image</h2>
				<img
					id="enhancedImage"
					src="https://placehold.co/400x300?text=Placeholder"
					alt="Enhanced"
				/>
			</div>
		</div>
	);
}

export default ImageViewer;
