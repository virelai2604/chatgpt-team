#Requires -RunAsAdministrator
# Restore-RXUltimate.ps1 — rebuilds the 'RX 9060 XT Ultimate' power plan tuning
# from VIRELAI's verified dumps, keeps processor attributes UNHIDDEN, activates it.
# Idempotent: safe to re-run after an Insider update wipes/resets the plan.

$rx = "99999999-9999-9999-9999-999999999999"
$ult = "f967965a-84ba-47d4-a274-1727ec0a8c42"

# 1) Ensure the plan exists; if missing, clone Ultimate into this exact GUID.
if (-not (powercfg /list | Select-String $rx)) {
    Write-Host "RX plan missing — cloning from Ultimate Performance..."
    powercfg -duplicatescheme $ult $rx 2>$null
    powercfg -changename $rx "RX 9060 XT Ultimate" "Maximum performance for RX 9060 XT"
}

# 2) Apply every tuned value that differs from stock Ultimate (AC + DC).
# --- Processor tuning ---
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 12a0ab44-fe28-4fa9-b3bd-4b64f44960a6 10  # Processor performance decrease threshold [DC] (was 30)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 40fbefc7-2e9d-4d25-a185-0cfd8574bac6 1  # Processor performance decrease policy [AC] (was 0)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 40fbefc7-2e9d-4d25-a185-0cfd8574bac6 1  # Processor performance decrease policy [DC] (was 0)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2  # Processor performance boost mode [AC] (was 1)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 2  # Processor performance boost mode [DC] (was 1)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6864 0  # Processor energy performance preference policy for Processor Power Efficiency Class 1 [DC] (was 50)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 97cfac41-2217-47eb-992d-618b1977c907 1000  # Processor performance core parking soft park latency [DC] (was 10)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 4d2b0152-7d5c-498b-88e2-34345392a2c5 15  # Processor performance time check interval [DC] (was 30)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 94d3a615-a899-4ac5-ae2b-e4d8f634367f 1  # System cooling policy [DC] (was 0)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318583 4  # Processor performance core parking min cores [AC] (was 50)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318583 4  # Processor performance core parking min cores [DC] (was 100)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964c 100  # Minimum processor state [AC] (was 30)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 465e1f50-b610-473a-ab58-00d1077dc418 2  # Processor performance increase policy [AC] (was 3)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 465e1f50-b610-473a-ab58-00d1077dc418 2  # Processor performance increase policy [DC] (was 0)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6863 5  # Processor energy performance preference policy [AC] (was 20)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6863 0  # Processor energy performance preference policy [DC] (was 50)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6865 0  # Processor energy performance preference policy for Processor Power Efficiency Class 2 [DC] (was 50)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 45bcc044-d885-43e2-8605-ee0ec6e96b59 100  # Processor performance boost policy [AC] (was 99)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 45bcc044-d885-43e2-8605-ee0ec6e96b59 100  # Processor performance boost policy [DC] (was 2)
powercfg /setacvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 06cadf0e-64ed-448a-8927-ce7bf90eb35d 30  # Processor performance increase threshold [AC] (was 40)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 06cadf0e-64ed-448a-8927-ce7bf90eb35d 30  # Processor performance increase threshold [DC] (was 90)
powercfg /setdcvalueindex $rx 54533251-82be-4824-96c1-47b60b740d00 943c8cb6-6f93-4227-ad87-e9a3feec08d1 60  # Processor performance core parking overutilization threshold [DC] (was 85)

# --- Disk / sleep / USB / display / wireless tuning ---
powercfg /setacvalueindex $rx 19cbb8fa-5279-450e-9fac-8a3d5fedd0c1 12bbebe6-58d6-4636-95bb-3217ef867c1a 0  # Power Saving Mode [AC] (was 3)
powercfg /setdcvalueindex $rx 9596fb26-9850-41fd-ac3e-f7c3c00afd4b 34c7b99f-9a6d-4b3c-8dc7-b6693b78cef4 0  # When playing video [DC] (was 1)
powercfg /setacvalueindex $rx 238c9fa8-0aad-41ed-83f4-97be242c8f20 bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 1  # Allow wake timers [AC] (was 0)
powercfg /setdcvalueindex $rx 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 1  # USB selective suspend setting [DC] (was 0)
powercfg /setdcvalueindex $rx 7516b95f-f776-4464-8c53-06167f40cc99 3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e 600  # Turn off display after [DC] (was 180)
powercfg /setdcvalueindex $rx 9596fb26-9850-41fd-ac3e-f7c3c00afd4b 10778347-1370-4ee0-8bbd-33bdacaade49 0  # Video playback quality bias [DC] (was 1)
powercfg /setdcvalueindex $rx 7516b95f-f776-4464-8c53-06167f40cc99 aded5e82-b909-4619-9949-f5d71dac0bcb 100  # Display brightness [DC] (was 75)
powercfg /setdcvalueindex $rx 238c9fa8-0aad-41ed-83f4-97be242c8f20 29f6c1db-86da-48c5-9fdb-f2b67b1f44da 0  # Sleep after [DC] (was 600)
powercfg /setacvalueindex $rx 0d7dbae2-4294-402a-ba8e-26777e8488cd 309dce9b-bef4-4119-9921-a851fb12f0f4 0  # Slide show [AC] (was 1)
powercfg /setdcvalueindex $rx 0d7dbae2-4294-402a-ba8e-26777e8488cd 309dce9b-bef4-4119-9921-a851fb12f0f4 0  # Slide show [DC] (was 1)
powercfg /setacvalueindex $rx 0012ee47-9041-4b5d-9b77-535fba8b1442 6738e2c4-e8a5-4a42-b16a-e040e769756e 0  # Turn off hard disk after [AC] (was 600)
powercfg /setdcvalueindex $rx 0012ee47-9041-4b5d-9b77-535fba8b1442 6738e2c4-e8a5-4a42-b16a-e040e769756e 1200  # Turn off hard disk after [DC] (was 0)

# 3) Keep processor attributes UNHIDDEN (so they stay editable in Control Panel).
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 06cadf0e-64ed-448a-8927-ce7bf90eb35d -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 06cadf0e-64ed-448a-8927-ce7bf90eb35e -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318583 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 0cc5b647-c1df-4637-891a-dec35c318584 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 12a0ab44-fe28-4fa9-b3bd-4b64f44960a6 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 12a0ab44-fe28-4fa9-b3bd-4b64f44960a7 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 12fd031f-53d2-4bf4-ac6d-c699fc9538c7 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 1a98ad09-af22-42ca-8e61-f0a5802c270a -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 1facfc65-a930-4bc5-9f38-504ec097bbc0 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 2430ab6f-a520-44a2-9601-f7f23b5134b1 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 2ddd5a84-5a71-437e-912a-db0b8c788732 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6863 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6864 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 36687f9e-e3a5-4dbf-b1dc-15eb381c6865 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 3b04d4fd-1cc7-4f23-ab1c-d1337819c4bb -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4009efa7-e72d-4cba-9edf-91084ea8cbc3 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 40fbefc7-2e9d-4d25-a185-0cfd8574bac6 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 40fbefc7-2e9d-4d25-a185-0cfd8574bac7 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 43f278bc-0f8a-46d0-8b31-9a23e615d713 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 447235c7-6a8d-4cc0-8e24-9eaf70b96e2b -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 447235c7-6a8d-4cc0-8e24-9eaf70b96e2c -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 45bcc044-d885-43e2-8605-ee0ec6e96b59 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 465e1f50-b610-473a-ab58-00d1077dc418 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 465e1f50-b610-473a-ab58-00d1077dc419 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4b70f900-cdd9-4e66-aa26-ae8417f98173 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4b70f900-cdd9-4e66-aa26-ae8417f98174 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4b70f900-cdd9-4e66-aa26-ae8417f98175 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4b92d758-5a24-4851-a470-815d78aee119 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4bdaf4e9-d103-46d7-a5f0-6280121616ef -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4d2b0152-7d5c-498b-88e2-34345392a2c5 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 4e4450b3-6179-4e91-b8f1-5bb9938f81a1 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 53824d46-87bd-4739-aa1b-aa793fac36d6 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 5ba7419a-295c-4b02-841b-66799388d6da -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 5d76a2ca-e8c0-402f-a133-2158492d58ad -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 603fe9ce-8d01-4b48-a968-1d706c28fd5c -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 603fe9ce-8d01-4b48-a968-1d706c28fd5d -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 603fe9ce-8d01-4b48-a968-1d706c28fd5e -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 60fbe21b-efd9-49f2-b066-8674d8e9f423 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 616cdaa5-695e-4545-97ad-97dc2d1bdd88 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 616cdaa5-695e-4545-97ad-97dc2d1bdd89 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 619b7505-003b-4e82-b7a6-4dd29c300971 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 619b7505-003b-4e82-b7a6-4dd29c300972 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 619b7505-003b-4e82-b7a6-4dd29c300973 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 64fcee6b-5b1f-45a4-a76a-19b2c36ee290 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 6788488b-1b90-4d11-8fa7-973e470dff47 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 69439b22-221b-4830-bd34-f7bcece24583 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 6c2993b0-8f48-481f-bcc6-00dd2742aa06 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 6ece9e1f-b6dd-42bf-b1b7-5a512b10c092 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 6ff13aeb-7897-4356-9999-dd9930af065f -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 71021b41-c749-4d21-be74-a00f335d582b -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 75b0ae3f-bce0-45a7-8c89-c9611c25e100 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 75b0ae3f-bce0-45a7-8c89-c9611c25e101 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 75b0ae3f-bce0-45a7-8c89-c9611c25e102 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 7b224883-b3cc-4d79-819f-8374152cbe7c -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 7d24baa7-0b84-480f-840c-1b0743c00f5f -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 7d24baa7-0b84-480f-840c-1b0743c00f60 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 7f2492b6-60b1-45e5-ae55-773f8cd5caec -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 7f2f5cfa-f10c-4823-b5e1-e93ae85f46b5 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 828423eb-8662-4344-90f7-52bf15870f5a -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964c -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964d -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 893dee8e-2bef-41e0-89c6-b55d0929964e -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 8baa4a8a-14c6-4451-8e8b-14bdbd197537 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 93b8b6dc-0698-4d1c-9ee4-0644e900c85d -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 943c8cb6-6f93-4227-ad87-e9a3feec08d1 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 94d3a615-a899-4ac5-ae2b-e4d8f634367f -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 97cfac41-2217-47eb-992d-618b1977c907 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 984cf492-3bed-4488-a8f9-4286c97bf5aa -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 984cf492-3bed-4488-a8f9-4286c97bf5ab -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 9943e905-9a30-4ec1-9b99-44dd3b76f7a2 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 b000397d-9b0b-483d-98c9-692a6060cfbf -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 b000397d-9b0b-483d-98c9-692a6060cfc0 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 b0deaf6b-59c0-4523-8a45-ca7f40244114 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 b28a6829-c5f7-444e-8f61-10e24e85c532 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 b669a5e9-7b1d-4132-baaa-49190abcfeb6 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 bae08b81-2d5e-4688-ad6a-13243356654b -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 bc5038f7-23e0-4960-96da-33abaf5935ec -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 bc5038f7-23e0-4960-96da-33abaf5935ed -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 bc5038f7-23e0-4960-96da-33abaf5935ee -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 be337238-0d82-4146-a960-4f3749d470c7 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 bf903d33-9d24-49d3-a468-e65e0325046a -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 c4581c31-89ab-4597-8e2b-9c9cab440e6b -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 c7be0679-2817-4d69-9d02-519a537ed0c6 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 cfeda3d0-7697-4566-a922-a9086cd49dfa -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 d8edeb9b-95cf-4f95-a73c-b061973693c8 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 d8edeb9b-95cf-4f95-a73c-b061973693c9 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 d92998c2-6a48-49ca-85d4-8cceec294570 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 dfd10d17-d5eb-45dd-877a-9a34ddd15c82 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 e0007330-f589-42ed-a401-5ddb10e785d3 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 ea062031-0e34-4ff1-9b6d-eb1059334028 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 ea062031-0e34-4ff1-9b6d-eb1059334029 -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 f735a673-2066-4f80-a0c5-ddee0cf1bf5d -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 f8861c27-95e7-475c-865b-13c0cb3f9d6b -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 f8861c27-95e7-475c-865b-13c0cb3f9d6c -ATTRIB_HIDE
powercfg -attributes 54533251-82be-4824-96c1-47b60b740d00 fddc842b-8364-4edc-94cf-c17f60de1c80 -ATTRIB_HIDE

# 4) Activate the plan and take a fresh backup.
powercfg /setactive $rx
powercfg /export "$env:USERPROFILE\Desktop\RX9060XT_Ultimate_backup.pow" $rx
Write-Host "Done. Active plan:"; powercfg /getactivescheme
