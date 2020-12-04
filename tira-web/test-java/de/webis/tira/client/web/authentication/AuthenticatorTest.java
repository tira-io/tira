package de.webis.tira.client.web.authentication;

import java.util.HashMap;
import java.util.Map;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;

import org.junit.Assert;
import org.junit.Test;
import org.mockito.Matchers;
import org.mockito.Mockito;
import org.mockito.invocation.InvocationOnMock;
import org.mockito.stubbing.Answer;

import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.storage.UsersStoreTest;

public class AuthenticatorTest {
	
	@Test
	public void testThatNullRequestIsNotSignedIn() throws Exception {
		HttpServletRequest request = request(null, null);
		
		Assert.assertFalse(isSignedIn(request));
		Assert.assertNull(signedInUser(request));
	}
	
	@Test
	public void testThatRequestWithGroupAndWithoutUserIsNotSignedIn() throws Exception {
		HttpServletRequest request = request(null, "vm-xyz");
		
		Assert.assertFalse(isSignedIn(request));
		Assert.assertNull(signedInUser(request));
	}
	
	@Test
	public void testThatRequestWithUserAndWithoutGroupIsSignedIn() throws Exception {
		HttpServletRequest request = request("foo-bar", null);
		
		Assert.assertTrue(isSignedIn(request));
		User user = signedInUser(request);
		
		Assert.assertEquals("no-vm-assigned", user.getUserName());
		Assert.assertEquals(0, user.getRolesCount());
	}
	
	@Test
	public void testThatRequestWithUserAndWithGroupIsSignedIn() throws Exception {
		HttpServletRequest request = request("foo-bar", "vm-foo-bar");
		
		Assert.assertTrue(isSignedIn(request));
		User user = signedInUser(request);
		
		Assert.assertEquals("no-vm-assigned", user.getUserName());
		Assert.assertEquals(0, user.getRolesCount());
	}
	
	@Test
	public void testThatRequestWithUserAndWithAdminGroupUsesTheAdminGroup() throws Exception {
		HttpServletRequest request = request("foo-bar", "vm-froebe");
		
		Assert.assertTrue(isSignedIn(request));
		User user = signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
		Assert.assertEquals("xy-this-password-does-not-exist", user.getUserPw());
		Assert.assertEquals("maik.froebe@does-not-exist", user.getEmail());
	}

	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsa,vm-froebe");
		
		Assert.assertTrue(isSignedIn(request));
		User user = signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
		Assert.assertEquals("xy-this-password-does-not-exist", user.getUserPw());
		Assert.assertEquals("maik.froebe@does-not-exist", user.getEmail());
	}
	
	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup2() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsa,vm-froebe,fdghdf");
		
		Assert.assertTrue(isSignedIn(request));
		User user = signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
		Assert.assertEquals("xy-this-password-does-not-exist", user.getUserPw());
		Assert.assertEquals("maik.froebe@does-not-exist", user.getEmail());
	}
	
	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup3() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsa,vm-froebe,vm-foobar,fdghdf");
		
		Assert.assertTrue(isSignedIn(request));
		User user = signedInUser(request);
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
		Assert.assertEquals("xy-this-password-does-not-exist", user.getUserPw());
		Assert.assertEquals("maik.froebe@does-not-exist", user.getEmail());
	}
	
	@Test
	public void testThatRequestWithUserAndMultipleGroupsGroupUsesTheAdminGroup4() throws Exception {
		HttpServletRequest request = request("foo-bar", ",,fdsavm-foobar,,vm-froebe,fdghdf");
		
		Assert.assertTrue(isSignedIn(request));
		User user = signedInUser(request);
		
		Assert.assertEquals("no-vm-assigned", user.getUserName());
		Assert.assertEquals(0, user.getRolesCount());
	}
	
	private boolean isSignedIn(HttpServletRequest req) throws ServletException {
		return Authenticator.isSignedIn(req, UsersStoreTest.USERS_STORE);
	}
	
	private User signedInUser(HttpServletRequest req) throws ServletException {
		return Authenticator.signedInUser(req, UsersStoreTest.USERS_STORE);
	}
	
	private static HttpServletRequest request(String userName, String groups) {
		Map<String, String> headers = new HashMap<>();
		headers.put("X-Disraptor-User", userName);
		headers.put("X-Disraptor-Groups", groups);
		
		return request(headers);
	}
	
	
	
	private static HttpServletRequest request(Map<String, String> headers) {
		HttpServletRequest ret = Mockito.mock(HttpServletRequest.class);
		
		Mockito.when(ret.getHeader(Matchers.anyString())).then(new Answer<String>() {
			@Override
			public String answer(InvocationOnMock i) throws Throwable {
				String arg = i.getArgumentAt(0, String.class);
				
				return headers.get(arg);
			}
		});
		
		return ret;
	}
}
