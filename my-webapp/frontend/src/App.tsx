import ButtonRow from "./components/controlPanel";
import ImageViewer from "./components/imageViewer";

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
