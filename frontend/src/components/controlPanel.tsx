import { useRef, useState } from "react";
import { useOCRStore } from "../store/useOCRStore";
import { BackendResponse, BoxResponse } from "../types/backendResponse";
import ImagePopup from "./ImagePopup";

// API endpoints configuration
const API_BASE_URL = "http://localhost:8000";
const API_ENDPOINTS = {
	BOX: (boxNumber: string) => `${API_BASE_URL}/box/${boxNumber}`,
	PROCESS_IMAGE: `${API_BASE_URL}/process-image`,
	UPDATE_RECORDS: `${API_BASE_URL}/update-records`,
};

interface ControlPanelProps {
	selectedFile: File | null;
	onFileSelect: (file: File | null) => void;
}

const ControlPanel = ({ selectedFile, onFileSelect }: ControlPanelProps) => {
	const [boxNumber, setBoxNumber] = useState("");
	const [imagePopupOpen, setImagePopupOpen] = useState(false);
	const fileInputRef = useRef<HTMLInputElement>(null);

	const setOCRResponse = useOCRStore((s) => s.setOCRResponse);
	const setPatientList = useOCRStore((s) => s.setPatientList);
	const setIsLoading = useOCRStore((s) => s.setIsLoading);
	const isLoading = useOCRStore((s) => s.isLoading);
	const undo = useOCRStore((s) => s.undo);
	const undoAll = useOCRStore((s) => s.undoAll);
	const history = useOCRStore((s) => s.history);
	const patientList = useOCRStore((s) => s.patientList);

	const handleSaveToSheet = async () => {
		if (patientList.length === 0) {
			alert("No records to save");
			return;
		}

		setIsLoading(true);
		try {
			// Get the current box number from the first patient
			const currentBoxNumber = patientList[0]?.box_number;

			// Save the records
			const response = await fetch(API_ENDPOINTS.UPDATE_RECORDS, {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(patientList),
			});

			if (!response.ok) {
				throw new Error(`Failed to save: ${response.statusText}`);
			}

			// If we have a box number, refresh the data for that box
			if (currentBoxNumber) {
				console.log("Refreshing box data...");
				const boxRes = await fetch(API_ENDPOINTS.BOX(currentBoxNumber), {
					method: "POST",
					headers: {
						Accept: "application/json",
						"Content-Type": "application/json",
					},
				});

				if (!boxRes.ok) {
					throw new Error(`Failed to refresh box data: ${boxRes.statusText}`);
				}

				const updatedPatients = await boxRes.json();
				setPatientList(updatedPatients);
				alert("Records saved successfully! Data has been refreshed.");
			} else {
				// If no box number, just clear the state
				setPatientList([]);
				setOCRResponse(null, "");
				alert("Records saved successfully!");
			}
		} catch (err) {
			const errorMessage =
				err instanceof Error ? err.message : "An unknown error occurred";
			alert(`Error saving records: ${errorMessage}`);
			console.error(err);
		} finally {
			setIsLoading(false);
		}
	};

	const handleGetBox = async () => {
		if (!boxNumber) return;
		setIsLoading(true);

		try {
			console.log("Fetching box data...");
			const boxRes = await fetch(API_ENDPOINTS.BOX(boxNumber), {
				method: "POST",
				headers: {
					Accept: "application/json",
					"Content-Type": "application/json",
				},
			});

			if (!boxRes.ok) {
				throw new Error(`Box search failed: ${boxRes.statusText}`);
			}

			const patients: BoxResponse = await boxRes.json();
			console.log("Received box data:", patients);
			setPatientList(patients);
		} catch (err) {
			const errorMessage =
				err instanceof Error ? err.message : "An unknown error occurred";
			alert(`Error: ${errorMessage}`);
			console.error(err);
			setPatientList([]);
		} finally {
			setIsLoading(false);
		}
	};

	const handleProcessImage = async () => {
		if (!selectedFile) return;
		console.log("Processing image:", selectedFile.name);
		setIsLoading(true);

		try {
			// Send image to /process-image
			console.log("Processing image...");
			const formData = new FormData();
			formData.append("file", selectedFile);

			const ocrRes = await fetch(API_ENDPOINTS.PROCESS_IMAGE, {
				method: "POST",
				body: formData,
			});

			if (!ocrRes.ok) {
				throw new Error(`OCR processing failed: ${ocrRes.statusText}`);
			}

			const ocrData = await ocrRes.json();
			console.log("Raw OCR response:", ocrData);

			// Backend now returns paddleOCR directly
			const transformedData: BackendResponse = {
				paddleOCR: ocrData.paddleOCR || [],
			};

			setOCRResponse(transformedData, selectedFile.name);
		} catch (err) {
			const errorMessage =
				err instanceof Error ? err.message : "An unknown error occurred";
			alert(`Error: ${errorMessage}`);
			console.error(err);
			setOCRResponse(null, "");
		} finally {
			setIsLoading(false);
		}
	};

	const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const file = e.target.files?.[0];
		if (file) {
			if (file.type.startsWith("image/")) {
				onFileSelect(file);
			} else {
				alert("Please select an image file");
				e.target.value = "";
			}
		}
	};

	return (
		<div className="control-panel-main">
			<div className="control-panel-center">
				<input
					type="text"
					className="text-input"
					placeholder="Enter Box Number (e.g., TCBOX77)"
					value={boxNumber}
					onChange={(e) => setBoxNumber(e.target.value.toUpperCase())}
					disabled={isLoading}
				/>
				<button
					className="control-panel-button"
					onClick={handleGetBox}
					disabled={!boxNumber || isLoading}
				>
					{isLoading ? "Loading..." : "Get Box"}
				</button>
				<input
					type="file"
					accept="image/*"
					ref={fileInputRef}
					style={{ display: "none" }}
					onChange={handleFileChange}
					disabled={isLoading}
				/>
				<button
					className="control-panel-button"
					onClick={() => fileInputRef.current?.click()}
					disabled={isLoading}
				>
					{selectedFile ? selectedFile.name : "Choose Image"}
				</button>
				<button
					className="control-panel-button"
					onClick={handleProcessImage}
					disabled={!selectedFile || isLoading}
				>
					{isLoading ? "Processing..." : "Send Image"}
				</button>
				<div className="divider"></div>
				<button
					className="control-panel-button secondary"
					onClick={undo}
					disabled={isLoading || history.length <= 1}
				>
					Undo
				</button>
				<button
					className="control-panel-button secondary"
					onClick={undoAll}
					disabled={isLoading || history.length <= 1}
				>
					Undo All
				</button>
				<div className="divider"></div>
				<button
					className="control-panel-button primary"
					onClick={handleSaveToSheet}
					disabled={isLoading || patientList.length === 0}
				>
					Save to Sheet
				</button>
			</div>
			<button
				className="image-popup-button"
				onClick={() => setImagePopupOpen(true)}
				disabled={!selectedFile || isLoading}
			>
				View Image
			</button>
			<ImagePopup
				file={selectedFile}
				open={imagePopupOpen}
				onClose={() => setImagePopupOpen(false)}
				anchorRight={true}
			/>
		</div>
	);
};

export default ControlPanel;
