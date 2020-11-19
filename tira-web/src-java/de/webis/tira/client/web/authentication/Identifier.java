package de.webis.tira.client.web.authentication;

import java.security.SecureRandom;

import org.apache.commons.lang3.RandomStringUtils;

public class Identifier {

	private static final SecureRandom SR = new SecureRandom();
	
	private static final char[] 
		CHARS = "0123456789abcdefghijklmnopqrstuvwxyz".toCharArray();
	
	public static final String nextId() {
		// TODO: Move length to configuration.
		return RandomStringUtils.random(32, 0, CHARS.length, true, true, CHARS,
				SR);
	}
	
}