import { useState, useMemo } from "react";
import ControlPanel from "./components/controlPanel";
import OCROutputs from "./components/OCROutputs";
import { useOCRStore } from "./store/useOCRStore";

function App() {
	const patientList = useOCRStore((s) => s.patientList);
	const ocrResponse = useOCRStore((s) => s.ocrResponse);
	const [selectedFile, setSelectedFile] = useState<File | null>(null);

	// Transform OCR response to match display format
	const ocrData = useMemo(() => {
		if (!ocrResponse) return [];

		console.log("Raw OCR Response:", ocrResponse.paddleOCR);

		// Filter and transform OCR results
		const filteredResults = ocrResponse.paddleOCR
			.filter((result) => {
				// Keep entries with a valid name (excluding special cases)
				return (
					result.name && result.name.trim() !== ""
					//result.name !== "tc851291199" possibly a default value, uncomment if so
				);
			})
			.map((result) => ({
				name: result.name.trim(),
				dob: result.dob || "",
				score: result.score || 0.9, // Default score if not provided
			}));

		console.log("Filtered OCR Data:", filteredResults);
		return filteredResults;
	}, [ocrResponse]);

	console.log("App Render State:", {
		patientListLength: patientList.length,
		ocrDataLength: ocrData.length,
		hasOcrResponse: !!ocrResponse,
		ocrData,
	});

	return (
		<div className="main-container">
			<div className="outputs-area">
				<OCROutputs boxData={patientList} selectedFile={selectedFile} />
			</div>
			<ControlPanel
				onFileSelect={setSelectedFile}
				selectedFile={selectedFile}
			/>
		</div>
	);
}

export default App;
