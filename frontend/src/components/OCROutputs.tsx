// This will be the new OCR outputs and LLM output table component
const OCROutputs = ({
	mainTableData = [],
	sideTableData = [],
}: {
	mainTableData?: any[];
	sideTableData?: any[];
}) => {
	// Helper to check if a row in mainTableData has a match in sideTableData
	const hasMatch = (row: any) => {
		// For now, match by name and dob (customize as needed)
		return sideTableData.some(
			(side) => side.name === row.name && side.dob === row.dob
		);
	};

	return (
		<div className="outputs-container">
			<div className="main-table-container">
				<table className="main-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>DOB</th>
							<th>Last Visit</th>
							<th>Taken From</th>
							<th>Placed In</th>
							<th>To Shred</th>
							<th>Date Shredded</th>
						</tr>
					</thead>
					<tbody>
						{mainTableData.map((row, i) => (
							<tr key={i} className={hasMatch(row) ? "" : "row-no-match"}>
								<td>{row.name}</td>
								<td>{row.dob}</td>
								<td>{row.last_visit}</td>
								<td>{row.taken_from}</td>
								<td>{row.placed_in}</td>
								<td>{row.to_shred ? "Yes" : "No"}</td>
								<td>{row.date_shredded}</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
			<div className="side-table-container">
				<table className="side-table">
					<thead>
						<tr>
							<th>LLM Output</th>
						</tr>
					</thead>
					<tbody>
						{sideTableData.map((row, i) => (
							<tr
								key={i}
								className={
									mainTableData.some(
										(main) => main.name === row.name && main.dob === row.dob
									)
										? ""
										: "row-no-match"
								}
							>
								<td>{`${row.name} - ${row.dob}`}</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		</div>
	);
};

export default OCROutputs;
