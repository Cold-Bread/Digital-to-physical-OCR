import ImageViewer from "./components/imageViewer";
import ButtonRow from "./components/controlPanel";

function App() {
	return (
		<div className="container">
			<h1 id="title" className="title">
				GReetings
			</h1>
			<ImageViewer />
			<ButtonRow />
		</div>
	);
}

export default App;
