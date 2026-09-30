SET NOCOUNT ON;
IF DB_ID(N'AssessmentMSSQL') IS NULL
    CREATE DATABASE AssessmentMSSQL;
GO

USE AssessmentMSSQL;
GO

IF OBJECT_ID(N'dbo.BroadcastEvents', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.BroadcastEvents (
        event_id bigint IDENTITY(1,1) NOT NULL CONSTRAINT PK_BroadcastEvents PRIMARY KEY,
        event_key nvarchar(100) NOT NULL CONSTRAINT UQ_BroadcastEvents_EventKey UNIQUE,
        title nvarchar(200) NOT NULL,
        recorded_at_utc datetime2(3) NOT NULL CONSTRAINT DF_BroadcastEvents_RecordedAt DEFAULT SYSUTCDATETIME(),
        video_bitrate_kbps int NOT NULL,
        audio_bitrate_kbps int NOT NULL,
        CONSTRAINT CK_BroadcastEvents_Bitrates CHECK (video_bitrate_kbps > 0 AND audio_bitrate_kbps > 0)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.BroadcastEvents WHERE event_key = N'assessment-seed-001')
BEGIN
    INSERT dbo.BroadcastEvents (event_key, title, video_bitrate_kbps, audio_bitrate_kbps)
    VALUES (N'assessment-seed-001', N'Thmanyah assessment broadcast sample', 12000, 192);
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.BroadcastEvents WHERE event_key = N'assessment-seed-001')
    THROW 51000, 'Expected assessment seed row is missing.', 1;
GO
