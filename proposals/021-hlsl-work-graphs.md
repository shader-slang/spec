# Proposal: Supporting HLSL Workgraphs Syntax in Slang

# Status

- **Status**: Design proposed and a review in progress.
- **Author**: Jae Kwak
- **Reviewers**: TBD
- **Related Issues/PRs**: 
  - Proposal Issue: [#6100](https://github.com/shader-slang/slang/issues/6100)
  - Partial implementation PR: [#6052](https://github.com/shader-slang/slang/pull/6052)
  - More to come...

# Background

HLSL Workgraphs provide a streamlined syntax for expressing hierarchical dispatch and cooperative thread group management. The proposal is to support the new HLSL semantics in a manner closely aligned with the syntax for HLSL Workgraphs.

Currently AMD proposed a SPIRV extension for Workgraphs. Slang will use the extension when targeting SPIR-V.

- [HLSL WorkGraphs (MS DirectX Spec)](https://microsoft.github.io/DirectX-Specs/d3d/WorkGraphs.html)
- [VK_AMDX_shader_enqueue Specification](https://docs.vulkan.org/features/latest/features/proposals/VK_AMDX_shader_enqueue.html)


# Proposed Implementation to Support the existing HLSL Syntax

> TLDR, Slang needs 13 new classes, 3 new attributes and a new pointer type to support a new storage-class.

New attributes and new classes are introduced in HLSL syntax to support the work-graphs. Slang will implement similar syntax to keep the compatibility.

 - Memory pointer to a new Storage-class, `NodePayloadAMDX`
   - NodePayloadPtr : required to support a storage-class, `NodePayloadAMDX`.
 - Launch mode
   - new capabilities
   - broadcasting launch mode
   - coalescing launch mode
   - thread launch mode
 - New shader attributes
   - [NodeLaunch("mode")] : "mode" can be "broadcasting", "coalescing" or "thread".
   - [MaxRecords(maxCount)] : defines the maximum amount of children that a node can launch.
   - [NodeDispatchGrid(x,y,z)] : define the number of thread groups to launch.
   - Other attributes not a part of this proposal
 - Input Record Objects
   - (RW)DispatchNodeInputRecord : input to Broadcasting launch node
   - (RW)GroupNodeInputRecords : input to Coalescing launch node used with `[MaxRecords(maxCount)]` on Coalescing launch to specify.
   - (RW)ThreadNodeInputRecord : input to Thread launch node
   - EmptyNodeInput : empty input used with `[MaxRecords(maxCount)]` on Coalescing launch to specify.
 - Output Node Objects
   - NodeOutput(Array) : Defines an output and record type for spawning nodes.
   - EmptyNodeOutput(Array) : Defines an empty output for spawning nodes with no record data.
 - Output Record Objects
   - ThreadNodeOutputRecord : set of zero or more records for each thread.
   - GroupNodeOutputRecords : et of one or more records with shared access across the thread group.

New barrier functions are introduced with work graphs in SM. But they are not a part of this proposal.


## Memory pointer to a new Storage-class, `NodePayloadAMDX`

HLSL defines that `Get()` methods to return a "reference" to a record data. However, `Get()` in Slang will return a pointer to the record data, instead, because there is no way to return a reference in Slang currently.

Similarly, HLSL defines that `NodeOutputArray::operator[]` and `EmptyNodeOutputArray ::operator[]` return a reference to `NodeOutput` and `EmptyNodeOutput` respectively, but Slang will return a pointer.

A new storage-class needs to be available in order to access the "record" objects.
```
__generic<T>
typealias NodePayloadPtr = Ptr<T, $( (uint64_t)AddressSpace::NodePayloadAMDX)>;
```

Whenenver the following methods need to return the "RecordType", it uses the new pointer type, `NodePayloadPtr<RecordType>`. It is because they are stored in "NodePayloadAMDX" storage-class.

## Launch mode

### New capability

Work graphs introduces three "Launch mode"-s: "thread", "broadcast and "coalescing". The HLSL syntax for the launch mode is:
```
[NodeLaunch("thread")],
[NodeLaunch("broadcasting")] or
[NodeLaunch("coalescing")]
```

Slang will add three capability atoms: thread, broadcasting and coalescing:
```
[require(hlsl_spirv, thread)],
[require(hlsl_spirv, broadcasting)] or
[require(hlsl_spirv, coalescing)]
```

### Broadcasting launch mode

Each input record initiates a full dispatch grid. The size of the dispatch grid can either be fixed for the node or specified in the input. Broadcasting launch mode is very similar to the traditional compute shader behavior.

Available node input:
 - `DispatchNodeInputRecord`
 - `RWDispatchNodeInputRecord`
 - `globallycoherent RWDispatchNodeInputRecord`

Available system value semantics:
 - `SV_GroupThreadID`
 - `SV_GroupIndex`
 - `SV_GroupID`
 - `SV_DispatchThreadID`

### Coalescing launch mode

A thread group operates on a shared array of input records. The shader declares the maximum number of records per thread group. 

Available node input:
 - `[MaxRecords(maxCount)] GroupNodeInputRecords`
 - `[MaxRecords(maxCount)] RWGroupNodeInputRecords`
 - `[MaxRecords(maxCount)] EmptyNodeInput`

Available system value semantics:
 - `SV_GroupThreadID`
 - `SV_GroupIndex`

### Thread launch mode

Each thread processes a single input record independently. Thread launch nodes have no visible thread group, do not require the numthreads attribute, have no access to group-shared memory, and cannot use group-scope memory or synchronization barriers.

Available node input:
 - `ThreadNodeInputRecord`
 - `RWThreadNodeInputRecord`


## New shader attributes

Many new attributes are introduced with Workgraphs. We are going to gradually implement them all. This proposal aims to implement the following a few required attributes.
 - [NodeLaunch("mode")]
 - [MaxRecords(maxCount)]
 - [NodeDispatchGrid(x,y,z)]

### [NodeLaunch("mode")]

"mode" can be "broadcasting", "coalescing" or "thread". Default if NodeLaunch attribute is not present is "broadcasting".

### [MaxRecords(maxCount)]

[MaxRecords(maxCount)] has two different meanings: one for input and another for output.

As a node input attribute, its description is following:
> Maximum record or EmptyNodeInput count for coalescing thread launch input. Default is 1 if unspecified.

As a node output attribute, its description is following:
> Given uint count declaration, the thread group can output 0...count records to this output. Exceeding this results in undefined behavior. For NodeArrayOutput, count applies across all the output nodes in the array (not count per node). This attribute can be overridden via the NumOutputOverrides / pOutputOverrides option when constructing a work graph as part of the definition of a node.


### [NodeDispatchGrid(x,y,z)]

Define the number of thread groups to launch for a BroadcastingLaunch node. In its absence, the node definition must declare it, or it must appear as `SV_DispatchGrid` in the input record - dynamic dispatch grid size. If the declaration appears in both the shader and the node definition, the definition in the node overrides. This attribute cannot be used if the launch mode is not BroadcastingLaunch.


### Other attributes and system semantics not a part of this proposal

The following attributes are **not** required and they are **not** a part of this proposal:
 - `[NodeIsProgramEntry]`: Designates a node as the entry point for a program, indicating that the node's shader function serves as the starting point for execution.
 - `[NodeID("nodeName")]`: Assigns a unique identifier to a node, allowing it to be referenced by name within the work graph.
 - `[NodeID("nodeName", arrayIndex)]`: Assigns a unique identifier to a node with a specified array index, enabling the identification of individual nodes within an array.
 - `[NodeLocalRootArgumentsTableIndex(index)]`: Specifies the index of the root arguments table for a node, facilitating the management of node-specific arguments.
 - `[NodeShareInputOf("nodeName")]`: Indicates that a node shares its input with another node identified by "nodeName," allowing for shared data access.
 - `[NodeShareInputOf("nodeName", arrayIndex)]`: Indicates that a node shares its input with a specific element of another node array, identified by "nodeName" and "arrayIndex."
 - `[NodeDispatchGrid(x, y, z)]`: Defines the dimensions of the dispatch grid for a node, specifying the number of threads in each dimension.
 - `[NodeMaxDispatchGrid(x, y, z)]`: Sets the maximum allowable dimensions for the dispatch grid of a node, providing constraints on grid size.
 - `[NodeMaxRecursionDepth(count)]`: Specifies the maximum depth of recursion allowed for a node, controlling the complexity of recursive operations.
 - `[NodeMaxInputRecordsPerGraphEntryRecord(count, sharedAcrossNodeArray)]`: Determines the maximum number of input records per graph entry record for a node, with an option to share inputs across a node array.
 - `[NodeTrackRWInputSharing]`: Enables tracking of read-write input sharing for a node, assisting in resource management and synchronization.
 - `[MaxRecordsSharedWith(nameInShader)]`: Specifies the maximum number of records that can be shared with another node identified by "nameInShader."
 - `[AllowSparseNodes]`: Permits the inclusion of nodes that may not have corresponding downstream nodes, allowing for more flexible and dynamic graph configurations.
 - `[NodeArraySize(count)]`: Defines the size of a node array, specifying the number of elements within the array.
 - `[UnboundedSparseNodes]`: Allows for nodes that can have an unbounded number of outputs, facilitating dynamic output generation.
 - `globallycoherent`: Indicates that a node's execution is globally coherent, ensuring consistent behavior across different invocations.


## Input Record Objects

### (RW)DispatchNodeInputRecord

```
/// read-only input to Broadcasting launch node
__generic<RecordType>
[require(hlsl_spirv, broadcasting)]
struct DispatchNodeInputRecord
{
    NodePayloadPtr<RecordType> Get();
};

/// shared read/write input to Broadcasting launch node
__generic_<RecordType>
[require(hlsl_spirv, broadcasting)]
struct RWDispatchNodeInputRecord
{
    NodePayloadPtr<RecordType> Get();
    bool FinishedCrossGroupSharing();
};
```

Record objects that only hold a single record (`{RW}DispatchNodeInputRecord` and `{RW}ThreadNodeInputRecord`) have a `Get()` method to access the contained record.
```
struct MyRecord { int field; };
DispatchNodeInputRecord<MyRecord> myRecord;
myRecord.Get().field; // access field from the record
```

For broadcasting launch nodes, where multiple thread groups can be launched for a given input record, `FinishedCrossGroupSharing()` can be optionally called on node input. The shader can make this call when a given thread group is finished reads and writes to it for the purpose of coordination across thread groups. 


### (RW)GroupNodeInputRecords

```
/// read-only input to Coalescing launch node used with [MaxRecords(maxCount)] on Coalescing launch to specify a count greater than 1
__generic<RecordType>
[require(hlsl_spirv, coalescing)]
struct GroupNodeInputRecords
{
    NodePayloadPtr<RecordType> Get(int index = 0);
    NodePayloadPtr<RecordType> __subscript(int index) { get; }
    int Count();
};

/// shared read/write input to Coalescing launch node used with [MaxRecords(maxCount)] on Coalescing launch to specify a count greater than 1
__generic_<RecordType>
[require(hlsl_spirv, coalescing)]
struct RWGroupNodeInputRecords
{
    NodePayloadPtr<RecordType> Get(int index = 0);
    NodePayloadPtr<RecordType> __subscript(int index) { get; set; }
    int Count();
};
```

Record objects that may hold more than one record (`{RW}GroupNodeInputRecords`, `{RW}ThreadNodeOutputRecords` and `{RW}GroupNodeOutputRecords`) have a `Get(int index=0)` method and an operator[] to access a contained record. The index parameter for the Get method defautls to 0, so it can be used the same way as for single-record access when only accessing the first record.
```
myRecords.Get().field; // access field from the first record
myRecords.Get(i).field; // access field from record at index i
myRecords[i].field; // access field from record at index i
```

`Count()` returns 1…maxCount for GroupNodeInputRecords, RWGroupNodeInputRecords, and EmptyNodeInput. It is the number of records that have been coalesced into the current thread group.


### (RW)ThreadNodeInputRecord

```
/// read-only input to Thread launch node
__generic<RecordType>
[require(hlsl_spirv, thread)]
struct ThreadNodeInputRecord
{
    NodePayloadPtr<RecordType> Get();
};

/// read/write input to Thread launch node
__generic<RecordType>
[require(hlsl_spirv, thread)]
struct RWThreadNodeInputRecord
{
    NodePayloadPtr<RecordType> Get();
};
```

### EmptyNodeInput

```
/// empty input used with [MaxRecords(maxCount)] on Coalescing launch to specify a count greater than 1
[require(hlsl_spirv, coalescing)]
struct EmptyNodeInput
{
    int Count();
};
```


## Output Node Objects

### NodeOutput(Array)

```
/// Defines an output and record type for spawning nodes
__generic<RecordType>
[require(hlsl_spirv, thread)]
struct NodeOutput
{
    NodePayloadPtr<ThreadNodeOutputRecords<RecordType>> GetThreadNodeOutputRecords();
    NodePayloadPtr<GroupNodeOutputRecords<RecordType>> GetGroupNodeOutputRecords();
    bool IsValid();
};

/// Defines an array of node outputs with a subscribe property.
[require(hlsl_spirv, thread)]
struct NodeOutputArray
{
    NodePayloadPtr<NodeOutput> __subscript(int index) { get; }
};
```

`IsValid()` indicates whether the specified output node is present in the work graph.


### EmptyNodeOutput(Array)

```
/// Defines an empty output for spawning nodes with no record data
[require(hlsl_spirv, broadcasting_coalescing_thread)]
struct EmptyNodeOutput
{
    void GroupIncrementOutputCount(uint count);
    void ThreadIncrementOutputCount(uint count);
    bool IsValid();
};

/// Defines an array of empty node outputs with a subscribe property.
[require(hlsl_spirv, broadcasting_coalescing_thread)]
struct EmptyNodeOutputArray
{
    NodePayloadPtr<EmptyNodeOutput> __subscript(int index) { get; }
};
```


## Output Record Objects

### ThreadNodeOutputRecords

```
/// set of zero or more records for each thread
__generic<RecordType>
[require(hlsl_spirv, thread)]
struct ThreadNodeOutputRecords
{
    NodePayloadPtr<RecordType> Get(int index = 0);
    NodePayloadPtr<RecordType> __subscript(int index) { get; }
    void OutputComplete();
};
```

### GroupNodeOutputRecords

```
/// set of one or more records with shared access across the thread group
__generic<RecordType>
[require(hlsl_spirv, coalescing_thread)]
struct GroupNodeOutputRecords
{
    NodePayloadPtr<RecordType> Get(int index = 0);
    NodePayloadPtr<RecordType> __subscript(int index) { get; }
    void OutputComplete();
};
```

After obtaining zero or more output records by calling Get{Group|Thread}NodeOutputRecords(), and a thread group is later finished using the returned ThreadNodeOutputRecords/GroupNodeOutputRecords object for writing a set of zero or more records, it must call `OutputComplete()` at least once once, otherwise behavior is undefined. 


# Examples

Below examples should compile after this proposal is implemented.

## Example 1: Hello world

```hlsl
struct RecordData
{
    int myData;
};

[Shader("node")]
[NodeLaunch("thread")]
void MyGraphRoot(
    [MaxRecords(1)] NodeOutput<RecordData> MyChildNode
)
{
    ThreadNodeOutputRecords<RecordData> childNodeRecord  MyChildNode.GetThreadNodeOutputRecords(1);
    childNodeRecord.Get(.myData = 123456;
    childNodeRecord.OutputComplete(;
}

[shader("node")]
[NodeLaunch("broadcasting")]
[NodeDispatchGrid(1, 1, 1)]
[numthreads(8, 8, 1)]
void MyChildNode(
    DispatchNodeInputRecord<RecordData> inputData,
    uint2 dispatchThreadId : SV_DispatchThreadID
)
{
    int myData = inputData.Get().myData;
}
```

## Example 2: D3D12HelloWorkGraphs

The following shader is from [D3D12HelloWorkGraphs.hlsl](https://github.com/microsoft/DirectX-Graphics-Samples/blob/e0d2d722b831ccc2d72c69d6c9a8a6e3c808f762/Samples/Desktop/D3D12HelloWorld/src/HelloWorkGraphs/D3D12HelloWorkGraphs.hlsl). For the purpose of the proposal, all comments are removed.

```
GlobalRootSignature globalRS = { "UAV(u0)" };
RWStructuredBuffer<uint> UAV : register(u0);

struct entryRecord
{
    uint gridSize : SV_DispatchGrid;
    uint recordIndex;
};

struct secondNodeInput
{
    uint entryRecordIndex;
    uint incrementValue;
};

struct thirdNodeInput
{
    uint entryRecordIndex;
};

static const uint c_numEntryRecords = 4;

[Shader("node")]
[NodeLaunch("broadcasting")]
[NumThreads(2,1,1)]
void firstNode(
    DispatchNodeInputRecord<entryRecord> inputData,
    [MaxRecords(2)] NodeOutput<secondNodeInput> secondNode,
    uint threadIndex : SV_GroupIndex,
    uint dispatchThreadID : SV_DispatchThreadID)
{
    GroupNodeOutputRecords<secondNodeInput> outRecs =
        secondNode.GetGroupNodeOutputRecords(2);

    outRecs[threadIndex].entryRecordIndex = inputData.Get().recordIndex;
    outRecs[threadIndex].incrementValue = dispatchThreadID*2 + threadIndex + 1;
    outRecs.OutputComplete();
}

[Shader("node")]
[NodeLaunch("thread")]
void secondNode(
    ThreadNodeInputRecord<secondNodeInput> inputData,
    [MaxRecords(1)] NodeOutput<thirdNodeInput> thirdNode)
{
    InterlockedAdd(UAV[inputData.Get().entryRecordIndex], inputData.Get().incrementValue);
    ThreadNodeOutputRecords<thirdNodeInput> outRec = thirdNode.GetThreadNodeOutputRecords(1);
    outRec.Get().entryRecordIndex = inputData.Get().entryRecordIndex;
    outRec.OutputComplete();
}

groupshared uint g_sum[c_numEntryRecords];

[Shader("node")]
[NodeLaunch("coalescing")]
[NumThreads(32,1,1)]
void thirdNode(
    [MaxRecords(32)] GroupNodeInputRecords<thirdNodeInput> inputData,
    uint threadIndex : SV_GroupIndex)
{
    if (threadIndex >= inputData.Count())
        return;
         
    for (uint i = 0; i < c_numEntryRecords; i++)
    {
        g_sum[i] = 0;
    }

    InterlockedAdd(g_sum[inputData[threadIndex].entryRecordIndex],1);

    if (threadIndex > 0)
        return;

    for (uint l = 0; l < c_numEntryRecords; l++)
    {
        uint recordIndex = c_numEntryRecords + l;
        InterlockedAdd(UAV[recordIndex],g_sum[l]);
    }
}
```

# Conclusion

This proposal outlines the necessary classes and method implementations for supporting HLSL workgraphs syntax in Slang using the SPIR-V AMD extension. The implementation will support both HLSL and SPIR-V targets. The design closely follows the DirectX WorkGraphs specification.


