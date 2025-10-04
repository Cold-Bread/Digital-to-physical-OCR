import { useState } from "react";
import ControlPanel from "./components/ControlPanel";
import OCROutputs from "./components/OCROutputs";
import { useOCRStore } from "./store/useOCRStore";

function App() {
	const patientList = useOCRStore((s) => s.patientList);
	const [selectedFile, setSelectedFile] = useState<File | null>(null);

	return (
		<div className="main-container">
			<OCROutputs boxData={patientList} selectedFile={selectedFile} />
			<ControlPanel
				onFileSelect={setSelectedFile}
				selectedFile={selectedFile}
			/>
		</div>
	);
}

export default App;
