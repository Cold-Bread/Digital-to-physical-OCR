import ControlPanel from "./components/controlPanel";
import ImageViewer from "./components/imageViewer";
import OCRPreview from "./components/OCRPreview";

function App() {
	return (
		<div className="main-container">
			<h1 className="title">Greetings</h1>
			<div className="content-layout">
				<ImageViewer />
				<ControlPanel />
				<OCRPreview />
			</div>
		</div>
	);
}

export default App;
