import { useState } from "react";
import ControlPanel from "./components/controlPanel";
import OCROutputs from "./components/OCROutputs";
import { useOCRStore } from "./store/useOCRStore";

function App() {
	const patientList = useOCRStore((s) => s.patientList);
	const [selectedFile, setSelectedFile] = useState<File | null>(null);

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
