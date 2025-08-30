import { useState } from "react";
import ControlPanel from "./components/controlPanel";
import OCROutputs from "./components/OCROutputs";
import { useOCRStore } from "./store/useOCRStore";

function App() {
	// Use global state for table data
	const patientList = useOCRStore((s) => s.patientList);
	const ocrResponse = useOCRStore((s) => s.ocrResponse);
	const ocrData = ocrResponse?.ocr1 || [];

	console.log('App Render State:', {
		patientListLength: patientList.length,
		ocrDataLength: ocrData.length,
		hasOcrResponse: !!ocrResponse
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
