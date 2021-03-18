package de.webis.tira.client.web.storage;

import java.io.File;

import org.junit.Assert;
import org.junit.Test;

import de.webis.tira.client.web.generated.TiraClientWebMessages.User;

public class UsersStoreTest {
	public static final UsersStore USERS_STORE = new UsersStore(new File("test-java/de/webis/tira/client/web/storage/test-user-store.prototext"));
	
	@Test
	public void checkNullIsReturnedForNonExistingUser() throws Exception {
		User user = USERS_STORE.getUserWithNameOrNull("does-not-exist");
		
		Assert.assertNull(user);
	}
	
	@Test
	public void checkNullIsReturnedForNullUser() throws Exception {
		User user = USERS_STORE.getUserWithNameOrNull(null);
		
		Assert.assertNull(user);
	}
	
	@Test
	public void checkDummyUserIsReturnedForUserWithoutVM() throws Exception {
		User user = USERS_STORE.getUserWithNameOrNull("no-vm-assigned");
		
		Assert.assertEquals("no-vm-assigned", user.getUserName());
		Assert.assertEquals(0, user.getRolesCount());
	}
	
	@Test
	public void checkReviewerUser() throws Exception {
		User user = USERS_STORE.getUserWithNameOrNull("froebe");
		
		Assert.assertEquals("froebe", user.getUserName());
		Assert.assertEquals(1, user.getRolesCount());
		Assert.assertEquals("reviewer", user.getRoles(0));
		Assert.assertEquals("xy-this-password-does-not-exist", user.getUserPw());
		Assert.assertEquals("maik.froebe@does-not-exist", user.getEmail());
	}
	
	@Test
	public void checkReviewerUserWithMistakeInUserName() throws Exception {
		User user = USERS_STORE.getUserWithNameOrNull(" froebe");

		Assert.assertNull(user);
	}
}
