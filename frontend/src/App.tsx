import { useState, useMemo } from "react";
import ControlPanel from "./components/controlPanel";
import OCROutputs from "./components/OCROutputs";
import { useOCRStore } from "./store/useOCRStore";
import { OCRResult } from "./types/backendResponse";

function App() {
	// Use global state for table data
	const patientList = useOCRStore((s) => s.patientList);
	const ocrResponse = useOCRStore((s) => s.ocrResponse);
	
	// Transform OCR response to match display format
	const ocrData = useMemo(() => {
		if (!ocrResponse?.ocr1) return [];

		console.log('Raw OCR Response:', ocrResponse.ocr1);

		// Filter and transform OCR results
		const filteredResults = ocrResponse.ocr1
			.filter(result => {
				// Keep entries with a valid name (excluding special cases)
				return result.name && 
					   result.name.trim() !== '' &&
					   result.name !== 'tc851291199';
			})
			.map(result => ({
				name: result.name.trim(),
				dob: result.dob || '',
				score: result.score || 0.9 // Default score if not provided
			}));

		console.log('Filtered OCR Data:', filteredResults);
		return filteredResults;
	}, [ocrResponse]);

	console.log('App Render State:', {
		patientListLength: patientList.length,
		ocrDataLength: ocrData.length,
		hasOcrResponse: !!ocrResponse,
		ocrData
	});

	const [selectedFile, setSelectedFile] = useState<File | null>(null);

	return (
		<div className="main-container">
			<div className="outputs-area">
				<OCROutputs
					boxData={patientList}
					ocrData={ocrData}
					selectedFile={selectedFile}
				/>
			</div>
			<ControlPanel onFileSelect={setSelectedFile} selectedFile={selectedFile} />
		</div>
	);
}

export default App;
