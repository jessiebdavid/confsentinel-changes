package org.confsentinel.engine.util;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.UUID;

public final class UuidV5Generator {

    public static final UUID NAMESPACE_CONFSENTINEL = UUID.fromString("a9e0f31c-5d82-4b2a-bf32-7c81604a11c2");

    private UuidV5Generator() {}

    /**
     * Implements RFC 4122 Version 5 (SHA-1 name-based UUID) for byte-for-byte parity with Python uuid.uuid5.
     */
    public static UUID generate(UUID namespace, String name) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            md.update(toBytes(namespace));
            md.update(name.getBytes(StandardCharsets.UTF_8));
            byte[] hash = md.digest();

            // Version 5 (bits 4-7 of time_hi_and_version set to 0101)
            hash[6] = (byte) ((hash[6] & 0x0f) | 0x50);
            // Variant RFC 4122 (bits 6-7 of clock_seq_hi_and_reserved set to 10)
            hash[8] = (byte) ((hash[8] & 0x3f) | 0x80);

            long msb = 0;
            long lsb = 0;
            for (int i = 0; i < 8; i++) msb = (msb << 8) | (hash[i] & 0xff);
            for (int i = 8; i < 16; i++) lsb = (lsb << 8) | (hash[i] & 0xff);

            return new UUID(msb, lsb);
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-1 algorithm unavailable", e);
        }
    }

    private static byte[] toBytes(UUID uuid) {
        long msb = uuid.getMostSignificantBits();
        long lsb = uuid.getLeastSignificantBits();
        byte[] buffer = new byte[16];
        for (int i = 0; i < 8; i++) buffer[i] = (byte) (msb >>> (8 * (7 - i)));
        for (int i = 8; i < 16; i++) buffer[i] = (byte) (lsb >>> (8 * (15 - i)));
        return buffer;
    }
}