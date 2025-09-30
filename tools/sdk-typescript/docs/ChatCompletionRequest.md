# ChatCompletionRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**model** | **string** |  | [default to undefined]
**messages** | [**Array&lt;ChatMessage&gt;**](ChatMessage.md) |  | [default to undefined]
**tools** | [**Array&lt;ToolDefinition&gt;**](ToolDefinition.md) |  | [optional] [default to undefined]
**tool_choice** | [**ChatCompletionRequestToolChoice**](ChatCompletionRequestToolChoice.md) |  | [optional] [default to undefined]

## Example

```typescript
import { ChatCompletionRequest } from './api';

const instance: ChatCompletionRequest = {
    model,
    messages,
    tools,
    tool_choice,
};
```

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)
