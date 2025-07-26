import { useEffect, useRef } from "react";
import { useOCRStore } from "../store/useOCRStore";

function ImageViewer() {
	const setResponse = useOCRStore((s) => s.setResponse);

	const originalImage = useOCRStore((s) => s.originalImage);
	const enhancedImage = useOCRStore((s) => s.enhancedImage);

	const fetchAndProcess = async () => {
		const res = await fetch("/api/process-image"); // <- Your backend endpoint
		const data = await res.json();
		setResponse(data);
	};

	useEffect(() => {
		const listener = (e: KeyboardEvent) => {
			if (e.key === "Enter") {
				fetchAndProcess();
			}
		};
		window.addEventListener("keydown", listener);
		return () => window.removeEventListener("keydown", listener);
	}, []);

	return (
		<div className="image-viewer">
			<img
				className="image-box"
				src={originalImage || "https://placehold.co/400x300?text=Original+Img"}
				alt="Original"
				width={300}
				height={300}
			/>
			<img
				className="image-box"
				src={enhancedImage || "https://placehold.co/400x300?text=Enhanced+Img"}
				alt="Enhanced"
				width={300}
				height={300}
			/>
		</div>
	);
}

export default ImageViewer;
