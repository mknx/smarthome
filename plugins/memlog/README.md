# MemLog

This plugins can be used to create in-memory logs which can be used by items or other
plugins.

# Requirements

No special requirements.

# Configuration

## plugin.conf

Use the plugin configuration to configure the in-memory logs.

<pre>
[memlog]
   class_name = MemLog
   class_path = plugins.memlog
   name = alert
#   maxlen = 50
</pre>

This will register a in-memory log with the name "alert". This can be used to attach 
to items.

## items.conf

The following attributes can be used.

### memlog

Defines the name of in-memory log which should be used to log the item's content to
the log.

### Example

Simple item logging:

<pre>
# items/my.conf

[some]
    [[item]]
        type = str
        memlog = alert
</pre>

## logic.conf

No logic configuration implemented.

# Methodes

No methods implemented.

