import { useRef, useState } from "react";
import { useOCRStore } from "../store/useOCRStore";

function ImageViewer() {
	const setOCR1 = useOCRStore((s) => s.setOCR1);
	const setOCR2 = useOCRStore((s) => s.setOCR2);
	const setOriginalImage = useOCRStore((s) => s.setOriginalImage);
	const originalImage = useOCRStore((s) => s.originalImage);
	const [loading, setLoading] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);

	const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (!file) return;
		setLoading(true);
		// Show preview
		const reader = new FileReader();
		reader.onload = (ev) => {
			setOriginalImage(ev.target?.result as string);
		};
		reader.readAsDataURL(file);

		// Send to PaddleOCR backend
		const formData = new FormData();
		formData.append("file", file);
		try {
			const paddleRes = await fetch("http://localhost:8001/ocr", {
				method: "POST",
				body: formData,
			});
			const paddleData = await paddleRes.json();
			setOCR1(paddleData.text || "No text detected");
		} catch (err) {
			setOCR1("Error contacting PaddleOCR backend");
		}

		// Send to TrOCR backend
		try {
			const trocrRes = await fetch("http://localhost:8002/ocr", {
				method: "POST",
				body: formData,
			});
			const trocrData = await trocrRes.json();
			setOCR2(trocrData.text || "No text detected");
		} catch (err) {
			setOCR2("Error contacting TrOCR backend");
		}

		setLoading(false);
	};

	return (
		<div className="image-viewer">
			<input
				type="file"
				accept="image/*"
				ref={fileInputRef}
				style={{ display: "none" }}
				onChange={handleFileChange}
			/>
			<button
				className="button"
				onClick={() => fileInputRef.current?.click()}
				disabled={loading}
			>
				{loading ? "Processing..." : "Upload Image & Run OCRs"}
			</button>
			<img
				className="image-box"
				src={originalImage || "https://placehold.co/400x300?text=Original+Img"}
				alt="Original"
				width={300}
				height={300}
			/>
		</div>
	);
}

export default ImageViewer;
