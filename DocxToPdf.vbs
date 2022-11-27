'Check if path was given as argument
If (WScript.Arguments.Count = 0) Then
	WScript.Echo "Missing path to folder containing .docx files"
	WScript.Quit 1
End If
sFolder = WScript.Arguments(0)

'Declare needed variables
Dim wordApplication
Dim wordDocument
Dim wordDocuments

'Set their values
Set oFSO = CreateObject("Scripting.FileSystemObject")
Set wordApplication = CreateObject("Word.Application")
Set wordDocuments = wordApplication.Documents

For Each oFile In oFSO.GetFolder(sFolder).Files
  If UCase(oFSO.GetExtensionName(oFile.Name)) = "DOCX" Then
	documentFile = sFolder + "\" + oFile.Name
	pdfOutputFile = sFolder + "\" + oFSO.GetBaseName(oFile.Name) + ".pdf"
	
	' Disable any potential macros of the word document.
	wordApplication.WordBasic.DisableAutoMacros
	
	Set wordDocument = wordDocuments.Open(documentFile)
	
	'Arguments for the export Call
	OutputFileName = pdfOutputFile
	ExportFormat = 17 			'wdExportFormatPDF
	OpenAfterExport = False
	OptimizeFor = 0 			'wdExportOptimizeForPrint
	Range = 0					'wdExportAllDocument
	DocFrom = 1
	DocTo = 1
	Item = 7					'wdExportDocumentWithMarkup
	IncludeDocProps = True
	KeepIRM = True
	CreateBookmarks = 2			'wdExportCreateWordBookmarks
	BitmapMissingFonts = True
	UseISO19005_1 = True
	wordDocument.ExportAsFixedFormat OutputFileName, ExportFormat, OpenAfterExport, OptimizeFor, Range, DocFrom, DocTo, Item, IncludeDocProps, KeepIRM, CreateBookmarks, BitmapMissingFonts, UseISO19005_1
	
	'Close document
	SaveChanges = 0				'wdDoNotSaveChanges
	wordDocument.Close SaveChanges
	
	'Clean up source .docx file
	oFSO.DeleteFile documentFile
  End if
Next

SaveChanges = 0				'wdDoNotSaveChanges
wordApplication.Quit SaveChanges

Set oFSO = Nothing
Set wordApplication = Nothing
Set wordDocument = Nothing
Set wordDocuments = Nothing



